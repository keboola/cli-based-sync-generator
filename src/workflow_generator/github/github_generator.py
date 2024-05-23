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
        envs = ', '.join(self.environments)
        manual = f" 1. Download generated Github CI/CD files in zip (button above).\n"
        manual += f" 2. Create a new Github repository.\n"
        manual += f" 3. Unpack Zip file and copy folder .Github to root of your repository.\n"
        manual += f" 4. Create all defined Environments ({envs}) in the Github repository settings.\n"
        manual += f"    - For sure, you can set allow ENV to the branch!\n"
        manual += f" 5. Setup all following Variables or Secret for all Environments.\n\n"
        manual += "| Detail | Variable | Secret |\n"
        manual += "| --- | --- | --- |\n"
        table_contents = []
        for project in self.projects:
            table_contents.append(f"| Set Keboola branch ID | 'KBC_BRANCH_ID_{project}' | |")
            table_contents.append(f"| Set Keboola project ID | 'KBC_PROJECT_ID_{project}' | |")
            table_contents.append(f"| Set Keboola storage API token | | 'KBC_STORAGE_API_TOKEN_{project}' |")
            table_contents.append(f"| Set Keboola stack URL | 'KBC_STORAGE_API_HOST_{project}' | |")
        table_contents.sort(reverse=True)
        manual += '\n'.join(table_contents)
        manual += '\n\n'
        manual += f" TODO next steps will be updated.! \n"
        manual += f" 6. Run manually Github workflow for pull all in your main branch.\n"
        manual += f" 7. Create all branches for your environments.\n"
        manual += f" 8. Run manually Github workflow for pull all in your other branch.\n"
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
                    "kbcStorageApiHost": f"KBC_STORAGE_API_HOST_{project}",
                    "kbcStorageApiToken": f"KBC_STORAGE_API_TOKEN_{project}",
                    "kbcProjectId": f"KBC_PROJECT_ID_{project}",
                    "kbcBranchId": f"KBC_BRANCH_ID_{project}"
                }
            }
            steps.append(step)
        return steps
