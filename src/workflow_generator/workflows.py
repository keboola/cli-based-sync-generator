from .base.workflow_generator import WorkflowGeneratorBase
from .github.github_generator import GithubGenerator

GITHUB_KEY = 'GitHub'
OUTPUT_DIR = "/OUTPUT"


class WorkflowGenerator:
    _platform: str
    _environments: dict[object]
    _project_mapping: dict[object]
    _generator: WorkflowGeneratorBase

    def __init__(self, root_path: str, platform: str, stack:str, environments: dict[object], project_mapping: dict[object]):
        self._platform = platform
        self._root_path = root_path
        self._stack = stack
        self._environments = environments
        self._project_mapping = project_mapping
        self._generator = self._get_generator()
        self._zip_file = self._generator.get_zip(f"{self._root_path}.{OUTPUT_DIR}", f"{self._platform}_workflows.zip")
        self._manual = self._generator.get_manual()

    def get_zip_file(self):
        return self._zip_file

    def get_manual(self) -> str:
        """Get manual for setting up the workflow"""
        return self._manual

    def _get_generator(self) -> WorkflowGeneratorBase:
        if self._platform == GITHUB_KEY:
            return GithubGenerator(self._root_path, self._stack, self._environments, self._project_mapping)
        else:
            raise ValueError(f"Unsupported platform yet...({self._platform})")
