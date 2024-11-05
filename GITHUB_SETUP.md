# GitHub Integration Setup for ConsultAIng

To use the GitHub integration features of ConsultAIng, you need to set up a GitHub Personal Access Token. Follow these steps:

1. Go to GitHub and log in to your account.

2. Click on your profile picture in the top-right corner and select "Settings" from the dropdown menu.

3. In the left sidebar, click on "Developer settings".

4. In the new left sidebar, click on "Personal access tokens", then "Tokens (classic)".

5. Click on "Generate new token", then "Generate new token (classic)".

6. Give your token a descriptive name in the "Note" field, e.g., "ConsultAIng Bot".

7. Set the expiration as per your security requirements.

8. Select the following scopes:
   - `repo` (Full control of private repositories)
   - `workflow` (Update GitHub Action workflows)

9. Scroll down and click "Generate token".

10. Copy the generated token immediately. You won't be able to see it again!

11. In your project's `.env` file, add the following line:
