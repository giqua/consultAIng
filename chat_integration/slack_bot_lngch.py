# slack_bot.py

import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from agent.graph.agent_graph import LangGraphAgent
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SlackBot:
    def __init__(self):
        self.app = App(token=os.environ["SLACK_BOT_TOKEN"])
        self.agent = LangGraphAgent()
        self.socket_mode_handler = None
        self.chat_histories = {}
        self.setup_event_handlers()

    def setup_event_handlers(self):
        @self.app.event("app_mention")
        def handle_mention(event, say):
            logger.info(f"Received mention: {event}")
            user_id = event["user"]
            text = event['text'].split('>', 1)[1].strip()
            self.handle_user_input(user_id, text, say)

        @self.app.event("message")
        def handle_message(event, say):
            logger.info(f"Received message: {event}")
            if event.get("channel_type") == "im":
                user_id = event["user"]
                text = event["text"]
                self.handle_user_input(user_id, text, say)

    def handle_user_input(self, user_id: str, text: str, say: callable):
        """Gestisce l'input dell'utente da Slack"""
        try:
            chat_history = self.chat_histories.get(user_id, [])
            
            # Processa il messaggio usando l'agente
            response = self.agent.process_message(text)
            
            # Aggiorna la chat history
            self.chat_histories[user_id] = chat_history + [
                {"role": "user", "content": text},
                {"role": "assistant", "content": response}
            ]
            
            # Invia la risposta
            say(f"<@{user_id}> {response}")
            
        except Exception as e:
            logger.error(f"Error handling user input: {str(e)}")
            say(f"<@{user_id}> Sorry, an error occurred: {str(e)}")

    def start(self):
        logger.info("Starting the bot...")
        self.socket_mode_handler = SocketModeHandler(self.app, os.environ["SLACK_APP_TOKEN"])
        logger.info("Bot started. To terminate the bot press ctrl+c") 
        self.socket_mode_handler.start()

    def stop(self):
        if self.socket_mode_handler:
            logger.info("Stopping the bot...")
            self.socket_mode_handler.close()
        logger.info("Bot stopped.")

    def run(self):
        try:
            self.start()
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            self.stop()