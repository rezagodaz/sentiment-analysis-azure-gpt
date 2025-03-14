import logging
from flask import Flask, render_template, request, jsonify
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from openai import OpenAI
from dotenv import load_dotenv
import os

# According to best practices, keys should not be hardcoded into the code. 
# Instead, they should be defined as environment variables for security purposes.
# I'll send them to the right person


load_dotenv()

AZURE_ENDPOINT=os.getenv('AZURE_ENDPOINT')
AZURE_API_KEY=os.getenv('AZURE_API_KEY')
AZURE_GPT_ENDPOINT=os.getenv('AZURE_GPT_ENDPOINT')
AZURE_GPT_KEY=os.getenv('AZURE_GPT_KEY')
DEPLOYMENT_ID=os.getenv('DEPLOYMENT_ID')
OPEN_AI_KEY=os.getenv('OPEN_AI_KEY')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

def get_text_analytics_client():
    """
    Initializes and returns an instance of the Azure Text Analytics Client.
    Returns:  TextAnalyticsClient: A client instance to interact with Azure Cognitive Services.
    """
    return TextAnalyticsClient(endpoint=AZURE_ENDPOINT, credential=AzureKeyCredential(AZURE_API_KEY))


def get_sentiment_result_from_azure(user_data):
    """
    Performs sentiment analysis on the given text using Azure Text Analytics.
    Args:      user_data (str): The input text to analyze.
    Returns:   dict: A dictionary containing sentiment label and confidence scores.
    """
    try:
        client = get_text_analytics_client()
        response = client.analyze_sentiment([user_data])
        result = response[0]  # Extract the first result

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

# Initialize OpenAI client
client = OpenAI(api_key=OPEN_AI_KEY)


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
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
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
    Handles sentiment analysis requests and generates an AI response.
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

    return jsonify({
        "azure": azure_result,
        "gpt": {"response": gpt_response}
    })


if __name__ == '__main__':
    app.run(debug=True)
