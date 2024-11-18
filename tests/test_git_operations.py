import unittest
from unittest.mock import patch, MagicMock
import os
from github import Github
from git import Repo
from github.GithubException import BadCredentialsException, UnknownObjectException
from agent.git_operations import stage_changes, commit_changes, push_changes, initialize_github_client, list_branches, create_new_branch, clone_repository
from agent.context_manager import ContextManager


class TestFileOperations(unittest.TestCase):

    @patch.dict(os.environ, {'GITHUB_TOKEN': 'dummy_token'})
    @patch('agent.git_operations.Github')
    def test_initialize_github_client_success(self, mock_github):
        mock_user = MagicMock()
        mock_user.login = 'test_user'
        mock_user.get_repos.return_value = ['repo1', 'repo2']
        mock_github.return_value.get_user.return_value = mock_user

        client = initialize_github_client()
        
        mock_github.assert_called_once_with('dummy_token')
        self.assertEqual(client, mock_github.return_value)
        mock_user.get_repos.assert_called_once()
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
    @patch('agent.git_operations.ContextManager')
    def test_create_new_branch(self, mock_context_manager, mock_init_client):
        mock_client = MagicMock()
        mock_repo = MagicMock()
        mock_base_branch = MagicMock()
        mock_base_branch.commit.sha = 'base_commit_sha'
        mock_repo.get_branch.return_value = mock_base_branch
        mock_client.get_repo.return_value = mock_repo
        mock_init_client.return_value = mock_client

        mock_cm_instance = MagicMock()
        mock_context_manager.return_value = mock_cm_instance
        mock_cm_instance.get_github_context.return_value = {'repo_name': 'test/repo', 'remote_url': 'https://github.com/test/repo.git'}


        result = create_new_branch('test/repo', 'main', 'new-feature', mock_cm_instance)
        
        self.assertTrue(result)
        mock_client.get_repo.assert_called_once_with('test/repo')
        mock_repo.get_branch.assert_called_once_with('main')
        mock_repo.create_git_ref.assert_called_once_with('refs/heads/new-feature', 'base_commit_sha')
        mock_cm_instance.update_github_context.assert_called_once_with(
            repo_name='test/repo',
            branch='new-feature',
            remote_url='https://github.com/test/repo.git'
        )
        mock_cm_instance.save_context.assert_called_once()
        print("test_create_new_branch passed")

    # @patch('agent.git_operations.os.path.exists')
    # @patch('agent.git_operations.os.makedirs')
    # @patch('agent.git_operations.Repo.clone_from')
    # def test_clone_repository(self, mock_clone_from, mock_makedirs, mock_exists):
    #     # Setup
    #     project_name = "test_project"
    #     remote_url = "https://github.com/user/test_project.git"
    #     mock_context_manager = MagicMock(spec=ContextManager)
    #     DEFAULT_PROJECTS_PATH = "/path/to/projects"

    #     # Mock os.path.exists to return False for the clone path and True for the projects directory
    #     mock_exists.side_effect = lambda path: path == DEFAULT_PROJECTS_PATH

    #     # Mock the cloned repo
    #     mock_repo = MagicMock(spec=Repo)
    #     mock_repo.working_dir = os.path.join(DEFAULT_PROJECTS_PATH, project_name)
    #     mock_repo.active_branch.name = "main"
    #     mock_clone_from.return_value = mock_repo

    #     # Call the function
    #     result = clone_repository(project_name, remote_url, mock_context_manager)

    #     # Assertions
    #     self.assertEqual(result, os.path.join(DEFAULT_PROJECTS_PATH, project_name))
    #     mock_clone_from.assert_called_once_with(remote_url, os.path.join(DEFAULT_PROJECTS_PATH, project_name))
    #     mock_context_manager.update_github_context.assert_called_once_with(
    #         repo_name=project_name,
    #         branch="main",
    #         remote_url=remote_url
    #     )
    #     mock_context_manager.save_context.assert_called_once()

    # @patch('agent.git_operations.os.path.exists')
    # def test_clone_repository_existing_directory(self, mock_exists):
    #     # Setup
    #     project_name = "existing_project"
    #     remote_url = "https://github.com/user/existing_project.git"
    #     mock_context_manager = MagicMock(spec=ContextManager)

    #     # Mock os.path.exists to return True for the clone path
    #     mock_exists.return_value = True

    #     # Call the function and check for raised exception
    #     with self.assertRaises(FileExistsError):
    #         clone_repository(project_name, remote_url, mock_context_manager)


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
