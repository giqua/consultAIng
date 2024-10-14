# agent/core.py

from openai import OpenAI
from dotenv import load_dotenv
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

class ConsultAIAgent:
    def __init__(self):
        logger.info("Initializing ConsultAIAgent")
        try:
            self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
            logger.info("OpenAI client initialized successfully")
        except KeyError:
            logger.error("OPENAI_API_KEY not found in environment variables")
            raise
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {e}")
            raise

    def process_message(self, message):
        logger.info(f"Processing message: {message[:50]}...")  # Log first 50 chars of message
        try:
            response = self.client.chat.completions.create(
                model=os.environ["OPENAI_MODEL"],
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant for software developers."},
                    {"role": "user", "content": message}
                ]
            )
            logger.info("Message processed successfully")
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "I'm sorry, I encountered an error while processing your message."

    def process_command(self, command, args):
        logger.info(f"Processing command: {command} with args: {args}")
        if command == 'review':
            return self.review_code(args['file'])
        elif command == 'generate':
            return self.generate_code(args['prompt'])
        else:
            logger.warning(f"Unknown command: {command}")
            return f"Unknown command: {command}"

    def review_code(self, file_path):
        logger.info(f"Reviewing code from file: {file_path}")
        try:
            with open(f'./temp_repo/{file_path}', 'r') as file:
                code = file.read()
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a code review assistant."},
                    {"role": "user", "content": f"Review this code:\n\n{code}"}
                ]
            )
            logger.info("Code review completed successfully")
            return response.choices[0].message.content
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return f"Error: File not found: {file_path}"
        except Exception as e:
            logger.error(f"Error reviewing code: {e}")
            return f"Error reviewing code: {str(e)}"

    def generate_code(self, prompt):
        logger.info(f"Generating code with prompt: {prompt[:50]}...")  # Log first 50 chars of prompt
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a code generation assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            logger.info("Code generation completed successfully")
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating code: {e}")
            return f"Error generating code: {str(e)}"

# Commented out update_repo method
# def update_repo(self, file_path, content):
#     logger.info(f"Updating repo: {file_path}")
#     try:
#         with open(f'./temp_repo/{file_path}', 'w') as file:
#             file.write(content)
#         self.repo.git.add(file_path)
#         self.repo.git.commit('-m', 'Update from ConsultAI')
#         self.repo.git.push()
#         logger.info("Repo updated successfully")
#     except Exception as e:
#         logger.error(f"Error updating repo: {e}")
#         raise
