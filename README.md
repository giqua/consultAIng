# ConsultAIng

## AI-Powered Assistant for Software Development Teams

ConsultAIng is an innovative AI-driven assistant designed to seamlessly integrate into your software development workflow. By leveraging natural language processing and machine learning, ConsultAIng enhances productivity, improves code quality, and streamlines the development process.

### Key Features

- **Natural Language Chat Interface**: Interact with the AI assistant using simple, conversational language.
- **Intelligent Code Assistance**: Get AI-powered code generation, optimization suggestions, and bug detection.
- **Automated Code Review**: Receive detailed feedback on code style, performance, and security.
- **Documentation Support**: Automatically generate and update code documentation and README files.
- **Testing Aide**: Get suggestions for test cases and auto-generated unit and integration tests.
- **Project Management Integration**: Manage tasks, track project status, and assist with sprint planning.
- **Version Control Support**: Seamlessly integrate with GitHub for commit messages, pull requests, and code merging.
- **Team Onboarding**: Provide project-specific information and best practices to new team members.

## Project Structure

- `agent/`: Core AI agent functionality
- `chat_integration/`: Slack bot integration
- `tests/`: Unit and integration tests

## Getting Started

1. Clone the repository:
    ``` bash
    git clone https://github.com/giqua/consultAIng.git cd ConsultAIng
    ```

2. Create a virtual environment and install dependencies:
    ``` bash
    python -m venv source venv/bin/activate
    pip install -r requirements.txt
    ```
3. Set up a Slack App:
    - Click "Create New App"
    - Choose "From an app manifest"
    - Select your workspace
    - Copy the contents of `slack_manifest.yaml` into the manifest editor
    - Review and create the app

4. Configure App Home and Permissions:
    - In your Slack App settings, go to "App Home"
    - Enable the "Messages Tab" and allow users to send messages
    - In "OAuth & Permissions", ensure you have the following scopes:
        - app_mentions:read
        - chat:write
        - im:history
        - im:read
        - im:write
5. Install the app to your workspace:
    - Go to "Install App" in the sidebar
    - Click "Install to Workspace" and authorize the app

6. Get your app tokens:
    - In "OAuth & Permissions", copy the "Bot User OAuth Token"
    - In "Basic Information" > "App-Level Tokens", create a new token with the `connections:write` scope
    - Copy the generated App-Level Token

7. Set up OpenAI API:
    - Go to https://platform.openai.com/ and create an account
    - Generate an API key

8. Create a `.env` file in the project root with the following content:
    ``` .env
    OPENAI_API_KEY=sk-.... 
    SLACK_BOT_TOKEN=xoxb-.... 
    SLACK_APP_TOKEN=xapp-....
    ```

9. Run the Slack bot:
    ``` bash
    python run_agent.py
    ```

## GitHub Integration

ConsultAIng includes features that integrate with GitHub. To set up the GitHub integration:

1. You'll need to create a GitHub Personal Access Token.
2. Add the token to your environment variables.

For detailed instructions on how to set up the GitHub integration, please refer to our [GitHub Setup Guide](GITHUB_SETUP.md).


## Usage

- In Slack, invite the bot to a channel
- Mention the bot in a channel or send a direct message to interact with it
- The bot will respond to your messages using AI-generated responses

## Extending the Bot

To add new features or modify the bot's behavior, edit the `agent/core.py` and `chat_integration/slack_bot.py` files.
The current implementation includes:

- Processing mentions and direct messages
- Generating responses using OpenAI's GPT model
- Basic error handling and logging

## Contributing

We welcome contributions to ConsultAIng! Please see our [Contributing Guide](CONTRIBUTING.md) for more details.

## License

ConsultAIng is released under the [MIT License](LICENSE).

### Contact

For any questions or support, please open an issue in this repository or contact our team at [email@consultaing.com](mailto:email@consultaing.com).

---

ConsultAIng - Empowering developers with AI-assisted software engineering.