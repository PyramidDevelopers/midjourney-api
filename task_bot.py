import os
import subprocess
from dotenv import load_dotenv
from exceptions import MissRequiredVariableError
import time

try:
    # Load environment variables from .env file
    load_dotenv()

    # Run aws_secrets.py using subprocess
    print("Running aws_secrets.py...")
    subprocess.run(["python", "aws_secrets.py"], check=True)

    # Add a delay (adjust as needed)
    print("Starting the bot")
    time.sleep(5)

    # After running aws_secrets.py, retrieve BOT_TOKEN
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise MissRequiredVariableError("Missing required environment variable: [BOT_TOKEN]")

    # Import the bot object after running aws_secrets.py
    print("Importing the bot object...")
    from task.bot.listener import bot

    if __name__ == '__main__':
        print("Running the bot...")
        bot.run(BOT_TOKEN)

except Exception as e:
    print(f"Error: {e}")
