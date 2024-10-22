import sys
import os
import signal

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chat_integration.slack_bot import SlackBot

def signal_handler(signum, frame):
    print("\nReceived signal to exit. Shutting down gracefully...")
    if bot:
        bot.stop()
    sys.exit(0)

if __name__ == "__main__":
    bot = None
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        bot = SlackBot()
        bot.run()
    except Exception as e:
        print(f"An error occurred: {e}")
    # finally:
    #     if bot:
    #         bot.stop()
    #     print("Bot has been shut down.")
    #     sys.exit(0)
