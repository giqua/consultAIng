from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from agent.core import ConsultAIAgent
from dotenv import load_dotenv
import os
import logging
from agent.context_manager import ContextManager
import threading
import agent.file_operations as file_operations

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

class SlackBot:
    def __init__(self):
        self.app = App(token=os.environ["SLACK_BOT_TOKEN"])
        self.agent = ConsultAIAgent()
        self.context_manager = ContextManager()
        self.socket_mode_handler = None
        self.setup_states = {}
        self.running = False
        self.setup_event_handlers()

    def setup_event_handlers(self):
        @self.app.event("app_mention")
        def handle_mention(event, say):
            logger.info(f"Received mention: {event}")
            user_id = event["user"]
            text = event['text'].split('>', 1)[1].strip()
            self.handle_user_input(user_id, text, say)

        @self.app.action("start_setup")
        def handle_start_setup(ack, body, say):
            logger.info("Starting setup process")
            ack()
            user_id = body["user"]["id"]
            say("Great! Let's set up a new project.")
            self.start_new_project_setup(user_id, say)

        @self.app.action("select_project")
        def handle_project_selection(ack, body, say):
            logger.info("Handling project selection")
            ack()
            selected_project = body["actions"][0]["selected_option"]["value"]
            self.context_manager.load_context(selected_project)
            say(f"Project '{selected_project}' has been loaded. You can now start working with this context.")
            say(f"To delete the current context, say cancel")

        @self.app.event("message")
        def handle_message(event, say):
            logger.info(f"Received message: {event}")
            if event.get("channel_type") == "im":
                user_id = event["user"]
                text = event["text"]
                self.handle_user_input(user_id, text, say)

    def start_new_project_setup(self, user_id, say):
        questions = self.context_manager.setup_new_project("")  # Temporary empty name
        if questions:
            self.setup_states[user_id] = {
                "step": "setup",
                "questions": questions,
                "current_question": 0
            }
            self.ask_next_question(user_id, say)
        else:
            say("There was an error setting up the project. Please try again.")

    def handle_user_input(self, user_id, text, say):
        if text.lower() == "cancel":
            self.handle_context_delete(user_id, say)
        elif text.lower() == "clone repository":
            self.start_repository_clone(user_id, say)
        elif user_id in self.setup_states:
            self.handle_setup_response(user_id, text, say)
        elif not self.context_manager.current_project:
            say("Hello! It looks like we haven't set up a project context yet.")
            self.start_project_selection(user_id, say)
        else:
            self.process_and_respond(text, user_id, say)
    
    def handle_context_delete(self, user_id, say):
        if user_id in self.setup_states or self.context_manager.current_project:
            context_info = self.context_manager.get_current_context() if self.context_manager.current_project else self.setup_states[user_id]
            
            confirmation_message = (
                "You're about to delete the following context:\n"
                f"```{context_info}```\n"
                "Are you sure you want to proceed? (Yes/No)"
            )
            say(confirmation_message)
            
            self.setup_states[user_id] = {"step": "confirm_delete", "context_info": context_info}
        else:
            say("There's no active context or setup process to cancel.")

    def start_project_selection(self, user_id, say):
        logger.info("Starting project selection")
        projects = self.context_manager.list_projects()
        if not projects:
            say("No existing projects found. Let's create a new one.")
            self.start_new_project_setup(user_id, say)
            return

        options = [
            {
                "text": {"type": "plain_text", "text": project},
                "value": project
            } for project in projects
        ]
        
        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "Please select an existing project or create a new one:"}
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "static_select",
                        "placeholder": {"type": "plain_text", "text": "Select a project"},
                        "options": options,
                        "action_id": "select_project"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Create New Project"},
                        "action_id": "start_setup"
                    }
                ]
            }
        ]
        say(blocks=blocks)

    def cancel_setup_process(self, user_id, say):
        if user_id in self.setup_states:
            del self.setup_states[user_id]
            say("Setup process cancelled. You can start over anytime.")
        else:
            say("There's no active setup process to cancel.")

    def handle_setup_response(self, user_id, text, say):
    # Log the start of the function
        logger.info(f"Handling setup response for user {user_id}")
        if text.lower() == "cancel":
        # Handle cancellation request
            logger.info(f"User {user_id} requested to cancel setup")
            self.cancel_setup_process(user_id, say)
        else:
            state = self.setup_states[user_id]
            if state["step"] == "confirm_delete":
                logger.info(f"Processing delete confirmation for user {user_id}")
                if text.lower() == "yes":
                    if self.context_manager.current_project:
                        project_name = self.context_manager.current_project
                        logger.info(f"Deleting context for project '{project_name}'")
                        self.context_manager.delete_context(project_name)
                        say(f"Context for project '{project_name}' has been deleted.")
                    else:
                        logger.info("Cancelling setup process and deleting temporary context")
                        say("Setup process cancelled and temporary context deleted.")
                    del self.setup_states[user_id]
                elif text.lower() == "no":
                    logger.info("User cancelled deletion")
                    say("Deletion cancelled. Your context remains unchanged.")
                    del self.setup_states[user_id]
                else:
                    logger.info("Invalid response for delete confirmation")
                    say("Please respond with 'Yes' or 'No'.")
                return

        # Handle setup questions
            elif state["step"] == "setup":
                question = state["questions"][state["current_question"]]
                param_path = f"{question['type']}.{question['field']}" if question['type'] else question['field']
                
                logger.info(f"Processing setup question: {param_path}")
            
            # Set project name if applicable
                if param_path == "project.name":
                    logger.info(f"Setting project name to: {text}")
                    self.context_manager.current_project = text
                
                # Set parameter in context manager
                logger.info(f"Setting parameter {param_path} to: {text}")
                self.context_manager.set_param(param_path, text)
                state["current_question"] += 1
                
                if state["current_question"] < len(state["questions"]):
                    logger.info("Moving to next setup question")
                    self.ask_next_question(user_id, say)
                else:
                    logger.info("Setup questions completed")
                    self.finish_setup(user_id, say)

        # Handle setting remote URL
            elif state["step"] == "set_remote_url":
                logger.info(f"Setting remote URL to: {text}")
                self.context_manager.set_param('version_control.remote_url', text)
                del self.setup_states[user_id]
                say(f"Remote URL set to: {text}")
                logger.info("Initiating repository clone")
                self.perform_repository_clone(say)

    def ask_next_question(self, user_id, say):
        state = self.setup_states[user_id]
        question = state["questions"][state["current_question"]]
        say(question["question"])

    def finish_setup(self, user_id, say):
        logger.info(f"Finishing setup for user {user_id}")
        try:
            self.context_manager.save_context()
            project_name = self.context_manager.current_project
            del self.setup_states[user_id]
            say(f"Great! Your project '{project_name}' context has been set up and saved. You can now start working with this context.")
            say("To delete the current context, type 'cancel'.")
        except ValueError as e:
            logger.error(f"Error saving context: {str(e)}")
            say(f"There was an error saving your project context: {str(e)}. Please try setting up the project again.")
            del self.setup_states[user_id]
    
    def start_repository_clone(self, user_id, say):
        # Log the start of the repository clone process
        logger.info(f"Starting repository clone process for user {user_id}")

        # Check if there's an active project context
        if not self.context_manager.has_active_context():
            logger.warning("No active project context found")
            say("No active project context. Please set up or select a project first.")
            return

        # Retrieve the remote URL from the context
        remote_url = self.context_manager.get_param('version_control.remote_url')
        logger.info(f"Retrieved remote URL: {remote_url}")

        if not remote_url:
            # If remote URL is not set, prompt the user to provide it
            logger.info("Remote URL not set, prompting user for input")
            say("Remote URL is not set. Please provide the repository URL:")
            # Set up the state to handle the user's response
            self.setup_states[user_id] = {"step": "set_remote_url"}
        else:
            # If remote URL is set, proceed with the repository clone
            logger.info("Remote URL is set, proceeding with repository clone")
            self.perform_repository_clone(self.context_manager.current_project, remote_url, say)
            # Log the completion of the function
            logger.info("Repository clone process completed")
    
    def perform_repository_clone(self, project_name, remote_url, say):
        try:
            result = file_operations.clone_repository(project_name, remote_url)
            say(f"Repository cloned successfully. {result}")
        except (ValueError, FileExistsError, RuntimeError) as e:
            say(f"Error cloning repository: {str(e)}")


    def process_and_respond(self, text, user, say):
        logger.info(f"Processing message from user {user}: {text}")
        current_context = self.context_manager.get_current_context()
        response = self.agent.process_message(text, current_context)
        logger.info(f"Sending response: {response[:50]}...")
        say(f"<@{user}> {response}")

    def start(self):
        logger.info("Starting the bot...")
        self.running = True
        self.socket_mode_handler = SocketModeHandler(self.app, os.environ["SLACK_APP_TOKEN"])
        logger.info("Bot started. To terminate the bot press ctrl+c") 
        self.socket_mode_handler.start()

    def stop(self):
        logger.info("Stopping the bot...")
        self.running = False
        if self.socket_mode_handler:
            self.socket_mode_handler.close()
        logger.info("Bot stopped.")

    def is_running(self):
        return self.running

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
    
    def run(self):
        self.start()
        while self.is_running():
            pass

# def start_bot():
#     bot = SlackBot()
#     try:
#         bot.run()
#     except KeyboardInterrupt:
#         print("\nInterrupted. Shutting down...")
#     finally:
#         bot.stop()

# if __name__ == "__main__":
#     start_bot()
