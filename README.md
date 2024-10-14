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
    python -m venv venv source venv/bin/activate
    pip install -r requirements.txt
    ```
3. Set up a Slack App:
    - Click "Create New App"
    - Choose "From an app manifest"
    - Select your workspace
    - Copy the contents of `slack_manifest.yaml` into the manifest editor
    - Review and create the app

4. Install the app to your workspace:
    - After creating the app, go to "Install App" in the sidebar
    - Click "Install to Workspace" and authorize the app

5. Get your app tokens:
    - In "OAuth & Permissions", copy the "Bot User OAuth Token"
    - In "Basic Information" > "App-Level Tokens", create a new token with the `connections:write` scope
    - Copy the generated App-Level Token

5. Set up OpenAI API:
    - Go to https://platform.openai.com/ and create an account
    - Generate an API key

6. Create a `.env` file in the project root with the following content:
    ``` .env
    OPENAI_API_KEY=your_openai_api_key 
    SLACK_BOT_TOKEN=your_slack_bot_token 
    SLACK_APP_TOKEN=your_slack_app_token
    ```
## Usage

- In Slack, invite the bot to a channel
- Mention the bot in a channel or send a direct message to interact with it
- The bot will respond to your messages using AI-generated responses

## Extending the Bot

To add new features or modify the bot's behavior, edit the `agent/core.py` and `chat_integration/slack_bot.py` files.

## Contributing

We welcome contributions to ConsultAIng! Please see our [Contributing Guide](CONTRIBUTING.md) for more details.

## License

ConsultAIng is released under the [MIT License](LICENSE).

### Contact

For any questions or support, please open an issue in this repository or contact our team at [email@consultaing.com](mailto:email@consultaing.com).

---

ConsultAIng - Empowering developers with AI-assisted software engineering.