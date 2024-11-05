import unittest
from unittest.mock import patch, MagicMock
import os
from github import Github
from agent.file_operations import initialize_github_client

class TestFileOperations(unittest.TestCase):

    @patch.dict(os.environ, {'GITHUB_TOKEN': 'dummy_token'})
    def test_initialize_github_client_success(self):
        client = initialize_github_client()
        self.assertIsInstance(client, Github, "Client should be an instance of Github")
        print("test_initialize_github_client_success passed")

    @patch.dict(os.environ, {})
    def test_initialize_github_client_no_token(self):
        with self.assertRaises(ValueError) as context:
            initialize_github_client()
        
        self.assertTrue('GITHUB_TOKEN environment variable is not set' in str(context.exception), "Exception message should mention missing token")
        print("test_initialize_github_client_no_token passed")

    @patch.dict(os.environ, {'GITHUB_TOKEN': 'dummy_token'})
    @patch('agent.file_operations.Github')
    def test_initialize_github_client_calls_github(self, mock_github):
        initialize_github_client()
        mock_github.assert_called_once_with('dummy_token')
        self.assertTrue(mock_github.called, "Github constructor should be called")
        print("test_initialize_github_client_calls_github passed")

if __name__ == '__main__':
    unittest.main(verbosity=2)
