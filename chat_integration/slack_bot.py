from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from agent.core import ConsultAIAgent
from dotenv import load_dotenv
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

app = App(token=os.environ["SLACK_BOT_TOKEN"])
agent = ConsultAIAgent()

@app.event("app_mention")
def handle_mention(event, say):
    logger.info(f"Received mention: {event}")
    user = event['user']
    text = event['text']
    # Remove the bot mention from the text
    text = text.split('>')[1].strip()
    process_and_respond(text, user, say)

@app.event("message")
def handle_message(event, say):
    logger.info(f"Received message: {event}")
    # Check if this is a direct message
    if event.get("channel_type") == "im":
        user = event['user']
        text = event['text']
        process_and_respond(text, user, say)

def process_and_respond(text, user, say):
    logger.info(f"Processing message from user {user}: {text}")
    response = agent.process_message(text)
    logger.info(f"Sending response: {response[:50]}...")  # Log first 50 chars of response
    say(f"<@{user}> {response}")

def start_bot():
    logger.info("Starting the bot...")
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()

if __name__ == "__main__":
    start_bot()
