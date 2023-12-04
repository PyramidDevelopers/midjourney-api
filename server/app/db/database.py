import json
import boto3
from botocore.exceptions import ClientError
import psycopg2
import os
from fastapi import UploadFile

class DatabaseConnection:
    def __init__(self, secret_name, region_name="us-east-1"):
        self.secret_name = secret_name
        self.region_name = region_name
        if os.getenv("PRODUCTION"):
            self.connection = self.get_postgres_connection_prod()
        else:
            self.connection = self.get_postgres_connection()

    def get_postgres_connection(self):
        try:
                connection = psycopg2.connect(
                    host=os.getenv('DEV_DB_HOST', 'postgres'),
                    database=os.getenv('DEV_DB_NAME', 'postgres'),
                    user=os.getenv('DEV_DB_USER', 'postgres'),
                    password=os.getenv('DEV_DB_PASSWORD', 'postgres'),
                    sslmode='disable'  # Local DB might not use SSL
                )
                return connection
        except (Exception, psycopg2.Error) as error:
                print("Error connecting to PostgreSQL database:", error)
                return None

    def get_postgres_connection_prod(self):
        # Create a Secrets Manager client
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=self.region_name
        )

        try:
            get_secret_value_response = client.get_secret_value(
                SecretId=self.secret_name
            )
        except ClientError as e:
            # Handle exceptions
            print(f"Error retrieving secret: {e}")
            return None

        # Decrypts secret using the associated KMS key.
        secret = get_secret_value_response['SecretString']

        # Parse the JSON secret string
        secret_dict = json.loads(secret)

        # Connect to the PostgreSQL database with SSL configuration
        try:
            connection = psycopg2.connect(
                host=secret_dict['host'],
                database=secret_dict['dbname'],
                user=secret_dict['username'],
                password=secret_dict['password'],
                sslmode='require'  # Use 'require' for SSL connection
            )

            return connection

        except (Exception, psycopg2.Error) as error:
            print("Error connecting to PostgreSQL database:", error)
            return None

    def close_connection(self):
        if self.connection:
            self.connection.close()

# Now you can use this utility in other parts of your code:

# Example usage:
# db_connection = DatabaseConnection(secret_name="prod/AthenaAI/postgres")
# connection = db_connection.connection
# if connection:
#     info = {"message_id": "123", "message_hash": "hash123", "content": "Hello", "url": "example.com", "proxy_url": "proxy.example.com"}
#     insert_into_prompts(info, connection)
#     records = get_records("messages", 123, connection)
#     print(records)
#
# # Don't forget to close the connection when done
# db_connection.close_connection()
