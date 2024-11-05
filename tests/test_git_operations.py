import unittest
from unittest.mock import patch, MagicMock
import os
from github import Github
from github.GithubException import BadCredentialsException, UnknownObjectException
from agent.git_operations import stage_changes, commit_changes, push_changes, initialize_github_client, list_branches, create_new_branch, clone_repository

class TestFileOperations(unittest.TestCase):

    @patch.dict(os.environ, {'GITHUB_TOKEN': 'dummy_token'})
    @patch('agent.git_operations.Github')
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
    @patch('agent.git_operations.Github')
    def test_initialize_github_client_invalid_credentials(self, mock_github):
        mock_github.return_value.get_user.side_effect = BadCredentialsException(status=401, data={}, headers={})
        
        with self.assertRaises(ValueError) as context:
            initialize_github_client()
        
        self.assertIn('Invalid GitHub credentials', str(context.exception))
        print("test_initialize_github_client_invalid_credentials passed")

    @patch.dict(os.environ, {'GITHUB_TOKEN': 'valid_token_no_permissions'})
    @patch('agent.git_operations.Github')
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
    @patch('agent.git_operations.Github')
    def test_initialize_github_client_unknown_object(self, mock_github):
        mock_github.return_value.get_user.side_effect = UnknownObjectException(status=404, data={}, headers={})
        
        with self.assertRaises(ValueError) as context:
            initialize_github_client()
        
        self.assertIn('Unable to retrieve user information. Check token permissions', str(context.exception))
        print("test_initialize_github_client_unknown_object passed")

    @patch('agent.git_operations.initialize_github_client')
    def test_list_branches(self, mock_init_client):
        mock_client = MagicMock()
        mock_repo = MagicMock()
        mock_branch1 = MagicMock()
        mock_branch1.name = 'main'
        mock_branch2 = MagicMock()
        mock_branch2.name = 'develop'
        mock_repo.get_branches.return_value = [mock_branch1, mock_branch2]
        mock_client.get_repo.return_value = mock_repo
        mock_init_client.return_value = mock_client

        branches = list_branches('test/repo')
        
        self.assertEqual(branches, ['main', 'develop'])
        mock_client.get_repo.assert_called_once_with('test/repo')
        mock_repo.get_branches.assert_called_once()
        print("test_list_branches passed")

    @patch('agent.git_operations.initialize_github_client')
    def test_create_new_branch(self, mock_init_client):
        mock_client = MagicMock()
        mock_repo = MagicMock()
        mock_base_branch = MagicMock()
        mock_base_branch.commit.sha = 'base_commit_sha'
        mock_repo.get_branch.return_value = mock_base_branch
        mock_client.get_repo.return_value = mock_repo
        mock_init_client.return_value = mock_client

        result = create_new_branch('test/repo', 'main', 'new-feature')
        
        self.assertTrue(result)
        mock_client.get_repo.assert_called_once_with('test/repo')
        mock_repo.get_branch.assert_called_once_with('main')
        mock_repo.create_git_ref.assert_called_once_with('refs/heads/new-feature', 'base_commit_sha')
        print("test_create_new_branch passed")

    @patch('agent.git_operations.initialize_github_client')
    @patch('agent.git_operations.Repo.clone_from')
    @patch('agent.git_operations.os.path.exists')
    def test_clone_repository(self, mock_exists, mock_clone_from, mock_init_client):
        mock_exists.return_value = False
        mock_repo = MagicMock()
        mock_repo.clone_url = 'https://github.com/test/repo.git'
        mock_client = MagicMock()
        mock_client.get_repo.return_value = mock_repo
        mock_init_client.return_value = mock_client

        result = clone_repository('test/repo', 'test_project')

        mock_init_client.assert_called_once()
        mock_client.get_repo.assert_called_with('test/repo')
        mock_clone_from.assert_called_with('https://github.com/test/repo.git', result)
        self.assertTrue(result.endswith('test_project'))
        print("test_clone_repository passed")


    @patch('agent.git_operations.Repo')
    def test_stage_changes_all(self, mock_repo):
        mock_instance = MagicMock()
        mock_repo.return_value = mock_instance

        result = stage_changes('/fake/path')

        mock_instance.git.add.assert_called_once_with(A=True)
        self.assertTrue(result)
        print("test_stage_changes_all passed")

    @patch('agent.git_operations.Repo')
    def test_stage_changes_specific_files(self, mock_repo):
        mock_instance = MagicMock()
        mock_repo.return_value = mock_instance

        files = ['file1.txt', 'file2.py']
        result = stage_changes('/fake/path', files)

        mock_instance.index.add.assert_called_once_with(files)
        self.assertTrue(result)
        print("test_stage_changes_specific_files passed")
    
    @patch('agent.git_operations.Repo')
    def test_commit_changes(self, mock_repo):
        mock_instance = MagicMock()
        mock_repo.return_value = mock_instance

        commit_message = "Test commit"
        result = commit_changes('/fake/path', commit_message)

        mock_instance.index.commit.assert_called_once_with(commit_message)
        self.assertTrue(result)
        print("test_commit_changes passed")
    
    @patch('agent.git_operations.Repo')
    def test_push_changes(self, mock_repo):
        mock_instance = MagicMock()
        mock_repo.return_value = mock_instance

        mock_remote = MagicMock()
        mock_instance.remote.return_value = mock_remote

        result = push_changes('/fake/path', 'origin', 'main')

        mock_instance.remote.assert_called_once_with(name='origin')
        mock_remote.push.assert_called_once_with(refspec='main:main')
        self.assertTrue(result)
        print("test_push_changes passed")
    
    @patch('agent.git_operations.Repo')
    def test_stage_changes_exception(self, mock_repo):
        mock_repo.side_effect = Exception("Git error")

        with self.assertRaises(RuntimeError):
            stage_changes('/fake/path')
        print("test_stage_changes_exception passed")
    
    @patch('agent.git_operations.Repo')
    def test_commit_changes_exception(self, mock_repo):
        mock_repo.side_effect = Exception("Git error")

        with self.assertRaises(RuntimeError):
            commit_changes('/fake/path', "Test commit")
        print("test_commit_changes_exception passed")

    @patch('agent.git_operations.Repo')
    def test_push_changes_exception(self, mock_repo):
        mock_repo.side_effect = Exception("Git error")

        with self.assertRaises(RuntimeError):
            push_changes('/fake/path')
        print("test_push_changes_exception passed")

if __name__ == '__main__':
    unittest.main()
