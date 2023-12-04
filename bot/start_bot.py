import os
import subprocess
from dotenv import load_dotenv
from util.exceptions import MissRequiredVariableError
import time
import subprocess

#try:
    # Load environment variables from .env file
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise MissRequiredVariableError("Missing required environment variable: [BOT_TOKEN]")

# Import the bot object after running aws_secrets.py
print("Importing the bot object...")
from task.bot.listener import bot

if __name__ == '__main__':
    print("Running the bot...")
    bot.run(BOT_TOKEN)

#except Exception as e:
#print(f"Error: {e}")
