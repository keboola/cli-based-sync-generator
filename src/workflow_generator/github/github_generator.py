from typing import List
import os
import shutil

from ..base.workflow_generator import WorkflowGeneratorBase, WorkflowTemplate

TEMPLATES_DIR = "/src/workflow_generator/github/_templates"
TEMPLATE_OUTPUT_DIR = "/src/workflow_generator/github/workflows"
ACTIONS_DIR = "/src/workflow_generator/github/actions"
GITIGNORE_FILE = "/src/workflow_generator/github/_additional_files/.gitignore"
OUTPUT_DIR = "/src/workflow_generator/github/generated_files"

# Define template configurations
templates = [
    {"template_file": "KBC_pull_all.yml.jinja", "filled_file": "KBC_pull_all.yml"},
    {"template_file": "KBC_push_all.yml.jinja", "filled_file": "KBC_push_all.yml"}
]


class GithubGenerator(WorkflowGeneratorBase):

    def __init__(self, root_path: str, environments: List[str], projects: List[str]):
        self.root_path = root_path
        self.environments = environments
        self.projects = projects
        self.template_data = {
            "projects": f"{', '.join(self.projects)}",
            "environment_spec": self._generate_environment_spec(),
            "steps": self._generate_steps()
        }
        self.templates = [
            WorkflowTemplate(self._add_root_path(TEMPLATES_DIR), template['template_file'],
                             self._add_root_path(TEMPLATE_OUTPUT_DIR),
                             template['filled_file']) for
            template
            in templates]
        super().__init__(root_path, self.template_data, self.templates)

    def _add_root_path(self, path: str):
        return f"{self.root_path}{path}"

    def get_manual(self):
        manual = f"Please create the following environments and secrets in your Github repository:\n"
        for project in self.projects:
            manual += (f"  1. Create a new environment with names of all your defined:"
                       f" '{[env for env in self.environments]}'\n")
            manual += f"  2. Set the branch ID as '{project}_BRANCH_ID' in the environment variables\n"
            manual += f"  3. Set the project ID as '{project}_PROJECT_ID' in the environment variables\n"
            manual += f"  4. Set the storage API token as '{project}_TOKEN' in the environment !secrets!\n"
            manual += f"  5. Set the stack URL as '{project}_STACK_URL' in the environment variables\n"
        return manual

    def get_zip(self, output_dir: str, zip_name: str):
        self._generate()
        folder_to_zip = f'{self._add_root_path(OUTPUT_DIR)}/'
        destination_folder = f'{folder_to_zip}.github/'

        if os.path.exists(destination_folder):
            shutil.rmtree(destination_folder)

        os.makedirs(destination_folder)

        shutil.copy(self._add_root_path(GITIGNORE_FILE), folder_to_zip)

        for source_folder in [self._add_root_path(TEMPLATE_OUTPUT_DIR), self._add_root_path(ACTIONS_DIR)]:
            if os.path.exists(source_folder):
                folder_name = os.path.basename(source_folder)

                destination_path = os.path.join(destination_folder, folder_name)

                shutil.copytree(source_folder, destination_path, dirs_exist_ok=True)

        return self._create_zip_file([folder_to_zip], output_dir, zip_name)

    def _generate_environment_spec(self):
        """
       Generates enviroment specification for Pull or Push operations
       """
        # Start the string with the special YAML syntax for literal block scalar
        environment_spec = "|-\n      ${{\n         "
        # Generate the conditions dynamically for each environment
        conditions = []
        for environment in self.environments:
            # For each environment, create a condition that matches the branch name with the environment name
            branch_name = 'main' if (environment == 'prod' or environment == 'production') else environment
            condition = f"github.ref_name == '{branch_name}' && '{environment}'"
            # Add the condition to the list
            conditions.append(condition)
        # Join all conditions with the logical OR operator, ensuring proper indentation and line breaks
        environment_spec += "\n      || ".join(conditions)
        environment_spec += "\n      }}"
        return environment_spec

    def _generate_steps(self):
        """
        Generates steps for Pull or Push operations based on the projects and operation type specified.
        """
        steps = []
        for project in self.projects:
            step = {
                "name": f"{project}",
                "with": {
                    "workdir": project,
                    "kbcStackUrl": f"{project}_STACK_URL",
                    "kbcStorageApiToken": f"{project}_TOKEN",
                    "kbcProjectId": f"{project}_PROJECT_ID",
                    "kbcBranchId": f"{project}_BRANCH_ID"
                }
            }
            steps.append(step)
        return steps
