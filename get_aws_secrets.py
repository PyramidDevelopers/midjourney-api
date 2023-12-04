import os
import boto3
import json
from dotenv import load_dotenv
from botocore.exceptions import ClientError

def update_env_with_secrets():
# AWS Secrets Manager configuration
    SECRET_NAME = "prod/AthenaAI/secrets"
    REGION_NAME = "us-east-1"

    load_dotenv()

    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

    if not aws_access_key_id:
        aws_access_key_id = input("Enter AWS Access Key ID: ")
    if not aws_secret_access_key:
        aws_secret_access_key = input("Enter AWS Secret Access Key: ")

    # Create a Secrets Manager client
    secrets_manager_client = boto3.client('secretsmanager', region_name=REGION_NAME, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

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
    basic_env_file_path = ".env.template"

    if os.path.exists(basic_env_file_path):
        with open(basic_env_file_path, 'r') as env_file:
            basic_lines = env_file.readlines()
        with open(env_file_path, 'w') as env_file:
            for line in basic_lines:
                env_file.write(line)
            for key in secrets:
                env_file.write(f"{key}={secrets[key]}\n")
            env_file.write(f"AWS_ACCESS_KEY_ID={aws_access_key_id}\n")
            env_file.write(f"AWS_SECRET_ACCESS_KEY={aws_secret_access_key}\n")
    else:
        print(f"Error: {basic_env_file_path} not found")
        exit(1)

    print("Credentials updated successfully.")

if __name__ == "__main__":
    update_env_with_secrets()