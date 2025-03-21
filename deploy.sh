#!/bin/bash

# Ensure gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud command not found. Install Google Cloud SDK."
    exit 1
fi

# Ensure user is authenticated
gcloud auth list &> /dev/null
if [ $? -ne 0 ]; then
    echo "Error: Not authenticated. Run 'gcloud auth login'."
    exit 1
fi

# Load .env file
ENV_FILE=".env"

if [[ ! -f "$ENV_FILE" || ! -r "$ENV_FILE" ]]; then
    echo "Error: .env file missing or unreadable."
    exit 1
fi

source $ENV_FILE

# Check required variables
REQUIRED_VARS=("GEN2" "RUNTIME" "REGION" "CLOUDFUNCTION" "SOURCE" "ENTRY_POINT" "MEMORY" "TIMEOUT" "PROJECT_ID" "SERVICE_ACCOUNT")
MISSING_VARS=()

for VAR in "${REQUIRED_VARS[@]}"; do
    if [[ -z "${!VAR}" ]]; then
        MISSING_VARS+=("$VAR")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo "Error: Missing required environment variables: ${MISSING_VARS[@]}"
    exit 1
fi

# Ensure the correct project is set
gcloud config set project $PROJECT_ID

# Deploy the function
gcloud functions deploy $CLOUDFUNCTION \
    --runtime=$RUNTIME \
    --region=$REGION \
    --source=$SOURCE \
    --entry-point=$ENTRY_POINT \
    --trigger-http \
    --memory=$MEMORY \
    --timeout=$TIMEOUT \
    --service-account=$SERVICE_ACCOUNT \
    --allow-unauthenticated \
    --set-env-vars PROJECT_ID=$PROJECT_ID,REGION=$REGION,CLOUDFUNCTION=$CLOUDFUNCTION

# Confirm deployment
gcloud functions describe $CLOUDFUNCTION --region=$REGION

echo "Deployment complete."
