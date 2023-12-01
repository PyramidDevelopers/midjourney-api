import os
import boto3
import json
from botocore.exceptions import ClientError

# AWS Secrets Manager configuration
SECRET_NAME = "prod/AthenaAI/secrets"
REGION_NAME = "us-east-1"

# Create a Secrets Manager client
secrets_manager_client = boto3.client('secretsmanager', region_name=REGION_NAME)

# Function to get the secret value from AWS Secrets Manager
def get_secret(secret_name):
    try:
        response = secrets_manager_client.get_secret_value(SecretId=secret_name)
        secret_string = response['SecretString']
        return secret_string
    except ClientError as e:
        print(f"Error retrieving secret '{secret_name}': {e}")
        raise

# Retrieve secrets from AWS Secrets Manager
secrets = json.loads(get_secret(SECRET_NAME))

# Path to the local .env file
env_file_path = ".env"

# Read existing content from the .env file
existing_lines = []
if os.path.exists(env_file_path):
    with open(env_file_path, 'r') as env_file:
        existing_lines = env_file.readlines()

# Update .env file with the secrets
with open(env_file_path, 'w') as env_file:
    for line in existing_lines:
        # Check if the line contains one of the keys to be replaced
        for key in ['OPENAI_API_KEY', 'CHANNEL_ID', 'GUILD_ID', 'BOT_TOKEN', 'USER_TOKEN']:
            if line.startswith(f"{key}="):
                # Replace the existing value with the secret value
                env_file.write(f"{key}={secrets[key]}\n")
                break
        else:
            # Preserve existing content if the line doesn't match any key
            env_file.write(line)

print("Credentials updated successfully.")
