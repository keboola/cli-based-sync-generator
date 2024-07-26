import base64
import os
import shutil
from pathlib import Path

from ..base.workflow_generator import WorkflowGeneratorBase, WorkflowTemplate

TEMPLATES_DIR = "src/workflow_generator/github/_templates"
TEMPLATE_OUTPUT_DIR = "src/workflow_generator/github/workflows"
ACTIONS_DIR = "src/workflow_generator/github/actions"
GITIGNORE_FILE = "src/workflow_generator/github/_additional_files/.gitignore"
OUTPUT_DIR = "src/workflow_generator/github/generated_files"

# Define template configurations
templates = [
    {"template_file": "KBC_pull_all.yml.jinja", "filled_file": "KBC_pull_all.yml"},
    {"template_file": "KBC_push_all.yml.jinja", "filled_file": "KBC_push_all.yml"}
]


class GithubGenerator(WorkflowGeneratorBase):

    def __init__(self, root_path: str, environments: dict[object], project_mapping: list[dict]):
        self._root_path = root_path
        self._projects = [project['project_name'] for project in project_mapping]
        self._environments = environments
        self._project_mapping = self._transform_mapping(project_mapping)
        print(self._environments)
        print(self._project_mapping)

        self._template_data = {
            "projects": f"{', '.join(self._projects)}",
            "environment_spec": self._generate_environment_spec(),
            "steps": self._generate_steps()
        }
        self._templates = [
            WorkflowTemplate(self._add_root_path(TEMPLATES_DIR), template['template_file'],
                             self._add_root_path(TEMPLATE_OUTPUT_DIR),
                             template['filled_file']) for
            template
            in templates]
        super().__init__(root_path, self._template_data, self._templates)

    def _transform_mapping(self, project_mapping: list[dict]) -> dict:
        """
        Converts the project mapping to a dictionary in convenient way
        project_name:env: {id: , link: }
        Args:
            project_mapping:

        Returns:

        """
        project_mapping_dict = {}
        for project in project_mapping:
            project_mapping_dict[project['project_name']] = {}
            for environment in self._environments:
                env_name = environment['env_name']
                project_mapping_dict[project['project_name']][env_name] = {}
                project_mapping_dict[project['project_name']][env_name]['id'] = project[f'{env_name}_id']
                project_mapping_dict[project['project_name']][env_name]['link'] = project[f'{env_name}_link']

        return project_mapping_dict

    def _add_root_path(self, path: str):
        return Path(self._root_path).joinpath(path).as_posix()

    def _get_env_md_list(self):
        return '\n - ' + '\n- '.join([environment['env_name'] for environment in self._environments])

    def _get_env_secrets_table_md(self) -> str:
        col_count = len(self._environments) + 1
        table_elements = []
        table_elements.append(f"| | {' | '.join([environment['env_name'] for environment in self._environments])} |\n")
        table_elements.append('| ' + ' | '.join(['---' for _ in range(col_count)]) + ' |\n')
        table_elements.append(
            '| **Variable Name** | ' + ' | '.join(['**Value**' for _ in range(col_count - 1)]) + ' |\n')
        for project in self._projects:
            cell_data = [f'*Storage token for project `{project}` in `{environment["env_name"]}`*' for environment in
                         self._environments]
            table_elements.append(
                f"| {project} | {' | '.join(cell_data)} |\n")

        return ''.join(table_elements)

    def _get_env_variables_table_md(self) -> str:
        col_count = len(self._environments) + 1
        table_elements = []
        table_elements.append(f"| | {' | '.join([environment['env_name'] for environment in self._environments])} |\n")
        cell_data = [f'`{environment["stack"]}`' for environment in self._environments]
        table_elements.append('| ' + ' | '.join(['---' for _ in range(col_count)]) + ' |\n')

        table_elements.append(
            '| **Variable Name** | ' + ' | '.join(['**Value**' for _ in range(col_count - 1)]) + ' |\n')
        table_elements.append(f"| SAPI_HOST | {' | '.join(cell_data)} |\n")

        for project in self._project_mapping:
            cell_data = [f'`{self._project_mapping[project][environment["env_name"]]["id"]}`' for environment in
                         self._environments]
            table_elements.append(
                f"| PROJECT_ID_{project} | {' | '.join(cell_data)} |\n")

        return ''.join(table_elements)

    def get_manual(self):
        manual_template = open(Path(TEMPLATES_DIR + "/github_manual.md"), "r").read()
        images = {
            "git_action_img_path": self._get_image_base64(Path(TEMPLATES_DIR + "/git_action.png")),
            "git_env_setup_img_path": self._get_image_base64(Path(TEMPLATES_DIR + "/git_env_setup.png")),
            "branch_protection_img_path": self._get_image_base64(Path(TEMPLATES_DIR + "/branch_protection.png"))
        }

        manual = manual_template.format(env_list=self._get_env_md_list(),
                                        env_secrets_table=self._get_env_secrets_table_md(),
                                        env_variables_table=self._get_env_variables_table_md(),
                                        **images)

        return manual

    @staticmethod
    def _get_image_base64(image_path):
        with open(image_path, "rb") as img_file:
            b64_string = base64.b64encode(img_file.read()).decode()
        return b64_string

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
        environment_spec = "${{"
        # Generate the conditions dynamically for each environment
        conditions = []
        for environment in self._environments:
            # For each environment, create a condition that matches the branch name with the environment name
            condition = f"github.ref_name == '{environment['branch']}' && '{environment['env_name']}'"
            # Add the condition to the list
            conditions.append(condition)
        # Join all conditions with the logical OR operator, ensuring proper indentation and line breaks
        environment_spec += " || ".join(conditions)
        environment_spec += " }}"
        return environment_spec

    def _generate_steps(self):
        """
        Generates steps for Pull or Push operations based on the projects and operation type specified.
        """
        steps = []
        for project in self._projects:
            step = {
                "name": f"{project}",
                "with": {
                    "workdir": project,
                    "kbcSapiHost": f"KBC_SAPI_HOST",
                    "kbcSapiToken": f"KBC_SAPI_TOKEN_{project}",
                    "kbcProjectId": f"KBC_PROJECT_ID_{project}",
                    "kbcBranchId": f"KBC_BRANCH_ID_{project}"
                }
            }
            steps.append(step)
        return steps
