import json
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ContextManager:
    def __init__(self, storage_dir='./contexts', template_file='contexts/templates/context_template.json'):
        self.storage_dir = storage_dir
        self.template_file = template_file
        self.current_context = None
        self.current_project = None
        os.makedirs(storage_dir, exist_ok=True)
        self.context_template = self.load_template()

    def update_github_context(self, repo_name, branch, remote_url):
        if 'version_control' not in self.current_context:
            self.current_context['version_control'] = {}
        
        self.current_context['version_control']['platform'] = 'GitHub'
        self.current_context['version_control']['repo_name'] = repo_name
        self.current_context['version_control']['current_branch'] = branch
        self.current_context['version_control']['remote_url'] = remote_url
        
        self.save_context()
        logger.info(f"Updated GitHub context for project: {self.current_project}")
    
    def get_github_context(self):
        return self.current_context.get('version_control', {})

    def clear_github_context(self):
        if 'version_control' in self.current_context:
            self.current_context['version_control'] = {
                'platform': None,
                'repo_name': None,
                'current_branch': None,
                'remote_url': None
            }
            self.save_context()
            logger.info(f"Cleared GitHub context for project: {self.current_project}")

    def load_template(self):
        try:
            with open(self.template_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Template file not found: {self.template_file}")

    def new_context(self, project_name):
        self.current_context = self._create_context_from_template(self.context_template)
        self.current_context['project']['name'] = project_name
        self.current_project = project_name
        logger.info(f"New context created for project: {self.current_project}")

    def _create_context_from_template(self, template):
        context = {}
        for key, value in template.items():
            if isinstance(value, dict):
                if 'value' in value:
                    context[key] = value['value']
                else:
                    context[key] = self._create_context_from_template(value)
            else:
                context[key] = value
        return context

    def delete_context(self, project_name):
        file_path = os.path.join(self.storage_dir, f"{project_name}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            if self.current_project == project_name:
                self.current_context = None
                self.current_project = None
        else:
            raise FileNotFoundError(f"No context found for project: {project_name}")

    def has_active_context(self):
        return self.current_context is not None and self.current_project is not None

    def save_context(self):
        if not self.current_context:
            raise ValueError("No active context to save: current_context is None")
        if not self.current_project:
            raise ValueError("No active context to save: current_project is None")
        file_path = os.path.join(self.storage_dir, f"{self.current_project}.json")
        with open(file_path, 'w') as f:
            json.dump(self.current_context, f, indent=2)

    def load_context(self, project_name):
        file_path = os.path.join(self.storage_dir, f"{project_name}.json")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"No context found for project: {project_name}")
        with open(file_path, 'r') as f:
            self.current_context = json.load(f)
        self.current_project = project_name

    def get_current_context(self):
        return self.current_context

    def list_projects(self):
        return [f.split('.')[0] for f in os.listdir(self.storage_dir) if f.endswith('.json')]

    def set_param(self, param_path, value):
        keys = param_path.split('.')
        d = self.current_context
        for key in keys[:-1]:
            if key not in d:
                d[key] = {}
            d = d[key]
        d[keys[-1]] = value

    def get_param(self, param_path=None):
        if not param_path:
            return self.current_context
        keys = param_path.split('.')
        d = self.current_context
        for key in keys:
            if key not in d:
                raise KeyError(f"Invalid key: {key}")
            d = d[key]
        return d

    def clear_param(self, param_path=None):
        if not param_path:
            self.__init__()  # Reset to initial empty state
            return
        keys = param_path.split('.')
        d = self.current_context
        for key in keys[:-1]:
            if key not in d:
                raise KeyError(f"Invalid key: {key}")
            d = d[key]
        if keys[-1] not in d:
            raise KeyError(f"Invalid key: {keys[-1]}")
        if isinstance(d[keys[-1]], dict):
            d[keys[-1]] = {k: None for k in d[keys[-1]]}
        elif isinstance(d[keys[-1]], list):
            d[keys[-1]] = []
        else:
            d[keys[-1]] = None

    def is_valid_key(self, param_path):
        try:
            self.get_param(param_path)
            return True
        except KeyError:
            return False

    def setup_new_project(self, project_name):
        logger.info(f"Setting up new project: {project_name}")
        self.new_context(project_name)
        return self._generate_questions(self.context_template)

    def _generate_questions(self, template, prefix=''):
        questions = []
        for key, value in template.items():
            if isinstance(value, dict):
                if 'value' in value and 'question' in value:
                    questions.append({
                        "type": prefix,
                        "field": key,
                        "question": value['question']
                    })
                else:
                    questions.extend(self._generate_questions(value, f"{prefix}.{key}" if prefix else key))
        return questions
