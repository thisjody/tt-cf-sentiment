import functions_framework
import os
import logging
import requests
from google.cloud import secretmanager

# Configure logging
logging.basicConfig(level=logging.INFO)

def get_secret(secret_name):
    """Retrieve a secret from Google Secret Manager and strip whitespace/newlines."""
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
def hello_gemini(request):
    """Simple test Cloud Function to connect to Gemini API and return a response."""
    try:
        gemini_api_key = get_secret("gemini-api-key")

        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-001:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": gemini_api_key  # ✅ Correct header for Gemini key auth
        }
        payload = {
            "contents": [
                {"parts": [{"text": "Hello, Gemini!"}]}
            ]
        }

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json(), 200

    except requests.exceptions.RequestException as e:
        logging.error(f"Network error connecting to Gemini API: {str(e)}")
        return {"error": "Failed to connect to Gemini API"}, 500
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return {"error": "An unexpected error occurred"}, 500