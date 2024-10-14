# agent/context_manager.py

import json
import os

class ContextManager:
    def __init__(self, config_file='project_config.json'):
        self.config_file = config_file
        self.context = self.load_context()

    def load_context(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {}

    def save_context(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.context, f, indent=2)

    def update_context(self, key, value):
        self.context[key] = value
        self.save_context()

    def get_context(self, key=None):
        if key:
            return self.context.get(key)
        return self.context

    def get_context_summary(self):
        return f"Project Context:\n" + \
               f"Language: {self.context.get('language', 'Not specified')}\n" + \
               f"Framework: {self.context.get('framework', 'Not specified')}\n" + \
               f"Coding Style: {self.context.get('coding_style', 'Not specified')}\n" + \
               f"Repository: {self.context.get('repository', 'Not specified')}"
