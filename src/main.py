import functions_framework
import os
import logging
import requests
from google.cloud import secretmanager

# Logging setup
logging.basicConfig(level=logging.INFO)

def get_secret(secret_name):
    """Retrieve a secret from Google Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.getenv("PROJECT_ID")
    secret_path = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    
    try:
        response = client.access_secret_version(name=secret_path)
        return response.payload.data.decode("UTF-8").strip()
    except Exception as e:
        logging.error(f"Error retrieving secret {secret_name}: {str(e)}")
        raise

@functions_framework.http
def analyze_sentiment(request):
    """Return Gemini hello AND Alpha Vantage news sentiment data."""
    try:
        # Secrets
        gemini_api_key = get_secret("gemini-api-key")
        alpha_key = get_secret("alpha-vantage-api-key")

        # Get ticker from request
        request_json = request.get_json(silent=True) or {}
        ticker = request_json.get("ticker", "AAPL")

        # -- 1. Call Gemini with basic "hello" prompt --
        gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-001:generateContent"
        gemini_headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": gemini_api_key
        }
        gemini_payload = {
            "contents": [
                {"parts": [{"text": "Hello, Gemini!"}]}
            ]
        }

        gemini_response = requests.post(gemini_url, headers=gemini_headers, json=gemini_payload)
        gemini_response.raise_for_status()
        gemini_data = gemini_response.json()
        gemini_reply = gemini_data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "No response")

        # -- 2. Call Alpha Vantage News Sentiment API --
        av_url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&apikey={alpha_key}"
        av_response = requests.get(av_url)
        av_response.raise_for_status()
        av_data = av_response.json()

        articles = []
        if "feed" in av_data:
            articles = [
                {
                    "headline": article.get("title"),
                    "summary": article.get("summary"),
                    "source": article.get("source", "Unknown"),
                    "sentiment_label": article.get("overall_sentiment_label"),
                    "sentiment_score": article.get("overall_sentiment_score")
                }
                for article in av_data["feed"][:5]
            ]

        # Return combined response
        return {
            "gemini_reply": gemini_reply,
            "ticker": ticker,
            "alpha_vantage_articles": articles
        }, 200

    except requests.exceptions.RequestException as e:
        logging.error(f"Network error: {str(e)}")
        return {"error": "Network error while calling Gemini or Alpha Vantage"}, 500
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return {"error": "Unexpected error occurred"}, 500
