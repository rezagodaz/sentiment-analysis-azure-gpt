# Sentiment Analysis with Azure and GPT APIs

This project is a web-based sentiment analysis application using **Flask**, **Azure AI Text Analytics**, and **OpenAI GPT APIs**. It analyzes user feedback, determines sentiment, and generates AI-driven responses based on the sentiment.

## Features

- Uses **Azure AI Text Analytics** to classify sentiment as Positive, Neutral, or Negative.
- Generates AI-powered responses using **GPT-3.5-turbo**.
- Built with **Flask** to provide a simple API endpoint.
- Supports easy deployment and dependency management.

## Project Structure

📂 sentiment-analysis-azure-gpt
│── 📂 templates/ # HTML templates (for web UI)
│── 📂 static/ # css files
│── 📜 app.py # Main Flask application
│── 📜 requirements.txt # Dependencies list
│── 📜 README.md # Documentation (you're reading it!)
│── 📜 .env.example # Example environment variables file

## 🛠 Installation

### 1 **Clone the Repository**

```sh
git clone https://github.com/rezagodaz/sentiment-analysis-azure-gpt.git
cd sentiment-analysis-azure-gpt
```

### 2️ **Create a Virtual Environment (Optional but Recommended)**

```sh
python -m venv venv
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate    # On Windows
```

### 3️ **Install Dependencies**

#### 🔹 Using `requirements.txt` (for pip users)

```sh
pip install -r requirements.txt
```

#### 🔹 Using `environment.yml` (for Conda users)

```sh
conda env create -f environment.yml
conda activate sentiment_env
```

## Setup API Keys

1. Create a `.env` file in the project directory and add your Azure and OpenAI keys:
   ```sh
   AZURE_ENDPOINT="https://your-azure-endpoint.cognitiveservices.azure.com/"
   AZURE_API_KEY="your-azure-api-key"
   OPENAI_API_KEY="your-openai-api-key"
   ```
2. Load environment variables automatically using `python-dotenv`.

## Running the Application

To start the Flask server, run:

```sh
python app.py
```

The application will be available at `http://127.0.0.1:5000/`.

## API Endpoints

### `POST /analyze`

**Request:**

```json
{
  "text": "This product is amazing!"
}
```

**Response:**

```json
{
  "azure": {
    "sentiment": "positive",
    "positive_score": 0.95,
    "neutral_score": 0.03,
    "negative_score": 0.02
  },
  "gpt": {
    "response": "Thank you for your kind words! We're thrilled that you loved the product."
  }
}
```

## License

This project is licensed under the **MIT License**.

---

🌟 **Feel free to contribute!** If you find any issues or want to enhance features, submit a PR or open an issue.
