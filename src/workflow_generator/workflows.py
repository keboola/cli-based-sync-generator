from pathlib import Path
import sys

path_root = Path(__file__)
print(str(path_root))
sys.path.append(str(path_root))

from .base.workflow_generator import WorkflowGeneratorBase
from .github.github_generator import GithubGenerator
from typing import List

GITHUB_KEY = 'github'
OUTPUT_DIR = "./app/OUTPUT"


class WorkflowGenerator:
    _platform: str
    _environments: List[str]
    _projects: List[str]
    _generator: WorkflowGeneratorBase

    def __init__(self, platform: str, environments: List[str], projects: List[str]):
        self._platform = platform
        self._environments = environments
        self._projects = projects
        self._generator = self._get_generator()
        self._zip_file = self._generator.get_zip(OUTPUT_DIR, f"{self._platform}_workflows.zip")
        self._manual = self._generator.get_manual()

    def get_zip_file(self):
        return self._zip_file

    def get_manual(self):
        return self._manual

    def _get_generator(self) -> WorkflowGeneratorBase:
        if self._platform == GITHUB_KEY:
            return GithubGenerator(self._environments, self._projects)
        else:
            raise ValueError(f"Unsupported platform: {self._platform}")
