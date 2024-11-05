import unittest
from unittest.mock import patch, MagicMock
import os
from github import Github
from github.GithubException import BadCredentialsException, UnknownObjectException
from agent.file_operations import initialize_github_client

class TestFileOperations(unittest.TestCase):

    @patch.dict(os.environ, {'GITHUB_TOKEN': 'dummy_token'})
    @patch('agent.file_operations.Github')
    def test_initialize_github_client_success(self, mock_github):
        mock_user = MagicMock()
        mock_user.login = 'test_user'
        mock_user.has_repo_scope.return_value = True
        mock_github.return_value.get_user.return_value = mock_user

        client = initialize_github_client()
        
        mock_github.assert_called_once_with('dummy_token')
        self.assertEqual(client, mock_github.return_value)
        mock_user.has_repo_scope.assert_called_once()
        print("test_initialize_github_client_success passed")

    @patch.dict(os.environ, {})
    def test_initialize_github_client_no_token(self):
        with self.assertRaises(ValueError) as context:
            initialize_github_client()
        
        self.assertTrue('GITHUB_TOKEN environment variable is not set' in str(context.exception), "Exception message should mention missing token")
        print("test_initialize_github_client_no_token passed")

    @patch.dict(os.environ, {'GITHUB_TOKEN': 'invalid_token'})
    @patch('agent.file_operations.Github')
    def test_initialize_github_client_invalid_credentials(self, mock_github):
        mock_github.return_value.get_user.side_effect = BadCredentialsException(status=401, data={}, headers={})
        
        with self.assertRaises(ValueError) as context:
            initialize_github_client()
        
        self.assertIn('Invalid GitHub credentials', str(context.exception))
        print("test_initialize_github_client_invalid_credentials passed")

    @patch.dict(os.environ, {'GITHUB_TOKEN': 'valid_token_no_permissions'})
    @patch('agent.file_operations.Github')
    def test_initialize_github_client_insufficient_permissions(self, mock_github):
        mock_user = MagicMock()
        mock_user.login = 'test_user'
        mock_user.has_repo_scope.return_value = False
        mock_github.return_value.get_user.return_value = mock_user
        
        with self.assertRaises(ValueError) as context:
            initialize_github_client()
        
        self.assertIn('GitHub token does not have required repository permissions', str(context.exception))
        print("test_initialize_github_client_insufficient_permissions passed")

    @patch.dict(os.environ, {'GITHUB_TOKEN': 'valid_token'})
    @patch('agent.file_operations.Github')
    def test_initialize_github_client_unknown_object(self, mock_github):
        mock_github.return_value.get_user.side_effect = UnknownObjectException(status=404, data={}, headers={})
        
        with self.assertRaises(ValueError) as context:
            initialize_github_client()
        
        self.assertIn('Unable to retrieve user information. Check token permissions', str(context.exception))
        print("test_initialize_github_client_unknown_object passed")


if __name__ == '__main__':
    unittest.main(verbosity=2)
