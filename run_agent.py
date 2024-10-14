import sys
import os

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chat_integration.slack_bot import start_bot

if __name__ == "__main__":
    start_bot()
