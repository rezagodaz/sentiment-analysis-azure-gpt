import os  
import base64
import logging
from flask import Flask, render_template, request, jsonify, url_for, send_from_directory
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from openai import OpenAI
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI  
from azure.identity import DefaultAzureCredential, get_bearer_token_provider  
from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, AudioConfig, audio, ResultReason, CancellationReason

# Final version
# According to best practices, keys should not be hardcoded into the code. 
# Instead, they should be defined as environment variables for security purposes.
# I'll send them to the right person

from dotenv import load_dotenv
load_dotenv()

AZURE_ENDPOINT=os.getenv('AZURE_ENDPOINT')
AZURE_API_KEY=os.getenv('AZURE_API_KEY')
AZURE_GPT_ENDPOINT=os.getenv('AZURE_GPT_ENDPOINT')
AZURE_GPT_KEY=os.getenv('AZURE_GPT_KEY')
DEPLOYMENT_ID=os.getenv("DEPLOYMENT_NAME", "gpt-35-turbo")
OPEN_AI_KEY=os.getenv('OPEN_AI_KEY')
AZURE_TEXT2SPEECH_KEY=os.getenv('AZURE_TEXT2SPEECH_KEY')

#UPLOAD_FOLDER = os.path.join(os.getcwd(),"static","audio")
UPLOAD_FOLDER = os.getcwd()
os.makedirs(UPLOAD_FOLDER, exist_ok=True) 


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['PREFERRED_URL_SCHEME'] = 'https'

def get_text_analytics_client():
    """
    Initializes and returns an instance of the Azure Text Analytics Client.
    Returns:  TextAnalyticsClient: A client instance to interact with Azure Cognitive Services.
    """
    return TextAnalyticsClient(endpoint=AZURE_ENDPOINT, credential=AzureKeyCredential(AZURE_API_KEY))


def get_sentiment_result_from_azure(user_data):
    """
    Performs sentiment analysis on the given text using Azure Text Analytics.
    """
    try:
        client = get_text_analytics_client()
        response = client.analyze_sentiment([user_data])  # Response is an iterable

        # Extracting the first item correctly
        result = next(iter(response), None)

        if result is None or hasattr(result, "error"):
            logger.error(f"Azure Sentiment Analysis Error: {result.error}")
            return {"error": "Sentiment analysis failed"}

        sentiment_data = {
            "sentiment": result.sentiment,
            "positive_score": result.confidence_scores.positive,
            "neutral_score": result.confidence_scores.neutral,
            "negative_score": result.confidence_scores.negative,
        }
        return sentiment_data
    except Exception as e:
        logger.error(f"Azure Sentiment Analysis Error: {str(e)}")
        return {"error": "Sentiment analysis failed"}


def generate_audio_response(sentiment, text):
    """
    Converts sentiment response to speech using Azure Speech API and saves the output as an audio file.
    Args:
        sentiment (str): The sentiment label (e.g., "positive", "negative", "neutral").
        text (str): The text to convert to speech.
    Returns:
        str: Path to the saved audio file.
    """
    # Set up Azure Speech Config
    speech_config = SpeechConfig(subscription=AZURE_TEXT2SPEECH_KEY, region="eastus2")
    
    # Set the voice and add sentiment using SSML
    voice_name = "en-US-AvaMultilingualNeural"
    ssml_text = f"""
    <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
        <voice name='{voice_name}'>
            <mood value='{sentiment}'/>
            {text}
        </voice>
    </speak>
    """

    # Save the output to a file
    output_file = f"output_{sentiment}.wav"  # Change to .wav if needed
    output_file_path = os.path.join(UPLOAD_FOLDER, output_file)
    audio_config = audio.AudioOutputConfig(filename=output_file_path)

    # Create a speech synthesizer
    speech_synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    # Synthesize the SSML
    speech_synthesis_result = speech_synthesizer.speak_ssml_async(ssml_text).get()

    # Check the result
    if speech_synthesis_result.reason == ResultReason.SynthesizingAudioCompleted:
        print(f"Speech synthesized for text [{text}] with sentiment [{sentiment}] and saved to {output_file}")
        return output_file, output_file_path
    elif speech_synthesis_result.reason == ResultReason.Canceled:
        cancellation_details = speech_synthesis_result.cancellation_details
        print(f"Speech synthesis canceled: {cancellation_details.reason}")
        if cancellation_details.reason == CancellationReason.Error:
            print(f"Error details: {cancellation_details.error_details}")
        return None


def generate_response(sentiment, feedback):
    """
    Generates an AI-powered response based on sentiment analysis results.
    Args: 
        sentiment (str): The sentiment label (positive, neutral, negative).
        feedback  (str): The original user feedback text.
    Returns:
        str: A generated response tailored to the sentiment.
    """

    prompt = f"Analyze this customer feedback: '{feedback}'\n"
    response_type = {
        "positive": "Generate a warm and appreciative response.",
        "neutral": "Generate a professional and informative response.",
        "negative": "Generate a polite and apologetic response with a constructive solution."
    }
    prompt += response_type.get(sentiment, "Generate a general response.")
    
    try:
        endpoint = os.getenv("ENDPOINT_URL", "https://rezagpt.openai.azure.com/")  
        #deployment = os.getenv("DEPLOYMENT_NAME", "gpt-4o-mini-audio-preview-2")  
        deployment =  DEPLOYMENT_ID 

        # Initialize Azure OpenAI Service client with key-based authentication    
        client = AzureOpenAI(  
            azure_endpoint=endpoint,  
            api_key=AZURE_GPT_KEY,  
            api_version="2024-05-01-preview",
        )

        response = client.chat.completions.create(
            model=deployment,
            #messages=chat_prompt,
            messages=[
                 {"role": "system", "content": "You are a customer support assistant."},
                 {"role": "user", "content": prompt}
             ]
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"GPT Response Error: {str(e)}")
        return "Error generating response."
    


# Flask Routes
@app.route('/')
def index():
    """
    Renders the index.html template for the web interface.
    Returns:  HTML: Rendered HTML template.
    """
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Handles sentiment analysis requests and generates an AI response. The audio is adjusted with the sentiment and emotions
    Expects JSON input:
    {
        "text": "User feedback text"
    }
    
    Returns: 
        JSON: Sentiment analysis results and AI-generated response.
    """
    
    data = request.json
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "No text provided"}), 400

    azure_result = get_sentiment_result_from_azure(text)
    if "error" in azure_result:
        return jsonify({"error": "Sentiment analysis failed"}), 500

    gpt_response = generate_response(azure_result["sentiment"], text)

    # Generate audio response
    #audio_filename, audio_full_filename = generate_audio_response(azure_result['sentiment'], gpt_response)

    
    #print(f"Audio file path: {audio_full_filename}")

    # if not os.path.exists(audio_full_filename):
    #     return jsonify({"error": "Audio generation failed"}), 500

    # Use only the filename, not the full path
    #audio_url = url_for('get_audio', filename=audio_filename, _external=True, _scheme='https')

    print(f"AZURE_TEXT2SPEECH_KEY {AZURE_TEXT2SPEECH_KEY}")
    return jsonify({
        "azure": azure_result,
        "gpt": {"response": gpt_response},
        "speech": AZURE_TEXT2SPEECH_KEY,
        "gpt_": AZURE_GPT_KEY,
        "end": AZURE_GPT_ENDPOINT,
        #"audio_url": audio_url
    })    

@app.route('/audio/<filename>')
def get_audio(filename):
    """Serve the generated audio file."""
    return send_from_directory(UPLOAD_FOLDER, filename, mimetype="audio/wav")


if __name__ == '__main__':
    app.run(debug=True)