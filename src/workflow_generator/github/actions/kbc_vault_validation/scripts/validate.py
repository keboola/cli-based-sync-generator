import argparse
import json
import logging
import os
import zipfile
from pathlib import Path

KEY_ORIGIN_SOURCE = "source"
KEY_ORIGIN_DESTINATION = "destination"

REPORT_FILE = "Vault_report.txt"


class ProjectFile:
    project: str
    path: str

    def __init__(self, project, path):
        self.project = project
        self.path = path


class ComparisonStructure:
    environment: str
    projects: list[ProjectFile]

    def __init__(self):
        self.environment: str = ''
        self.projects: list[ProjectFile] = []

    def get_projects(self):
        return set(project.project for project in self.projects)

    def get_project(self, project):
        for p in self.projects:
            if p.project == project:
                return p
        return None


class VaultDiff:
    source_structure: ComparisonStructure
    destination_structure: ComparisonStructure

    def __init__(self, workdir):
        logging.info(f"Vault comparison running... structure folder: '{workdir}'.")
        workdir = self._check_workdir(workdir)
        self.source_structure, self.destination_structure = self._create_objects_from_structure(workdir)

        if self.source_structure.get_projects() != self.destination_structure.get_projects():
            raise ValueError("Projects in source and destination structures do not match!")

        text_output = [f"Vault Comparison Result ('{self.source_structure.environment}' "
                       f"vs '{self.destination_structure.environment}')"]
        text_output.append(self._generate_line(text_output, '='))
        for source_project in self.source_structure.projects:
            destination_project = self.destination_structure.get_project(source_project.project)

            logging.info(f"Comparing source project {source_project.project} "
                         f"vs destination {destination_project.project}")

            text_output.append(f"\nSource project '{source_project.project}' "
                               f"vs Destination project '{destination_project.project}'")
            text_output.append(self._generate_line(text_output))
            text_output.extend(self._compare_structure(source_project.path, destination_project.path))

        text_output.append(f"\n{'-' * 50}\n\n")
        self._write_report(text_output)

    @staticmethod
    def _generate_line(text_list, character='-'):
        last_item = text_list[-1]
        last_item_length = len(last_item)

        line = f"{character * last_item_length}\n"

        return line

    @staticmethod
    def _compare_structure(source_project_path, destination_project_path):
        source = VaultDiff._read_file(source_project_path)
        destination = VaultDiff._read_file(destination_project_path)

        missing_in_source = [item for item in destination if item not in source]
        missing_in_destination = [item for item in source if item not in destination]

        text_lines = []
        if len(missing_in_source) > 0:
            missing_in_source_text = "\n".join(missing_in_source)
            text_lines.append(f"- In source project is missing following keys:\n{missing_in_source_text}\n")

        if len(missing_in_destination) > 0:
            missing_in_destination_text = "\n".join(missing_in_destination)
            text_lines.append(f"- In destination project is missing following keys:\n{missing_in_destination_text}\n")

        if not text_lines:
            return ["Vault structure is the same - No changes detected\n"]

        return text_lines

    @staticmethod
    def _write_report(text_output):
        with open(REPORT_FILE, 'w') as f:
            f.write('\n'.join(text_output))
        logging.info(f"Report written to {REPORT_FILE}")

    def _check_workdir(self, workdir):
        if not os.path.exists(workdir):
            raise FileNotFoundError(f"Workdir file {workdir} not found")

        if workdir.endswith('.zip'):
            workdir = self._unzip_dir(workdir)

        return workdir

    @staticmethod
    def _create_objects_from_structure(base_path):
        base_path = Path(base_path)
        source = ComparisonStructure()
        destination = ComparisonStructure()

        for origin_path in base_path.iterdir():
            if origin_path.is_dir():
                for env_path in origin_path.iterdir():
                    if env_path.is_dir():
                        env = env_path.name

                        for file_path in env_path.glob('*.json'):
                            proj = ProjectFile(file_path.stem, str(file_path))

                            if origin_path.name == KEY_ORIGIN_SOURCE:
                                if not source.environment:
                                    source.environment = env
                                source.projects.append(proj)
                            elif origin_path.name == KEY_ORIGIN_DESTINATION:
                                if not destination.environment:
                                    destination.environment = env
                                destination.projects.append(proj)

        return source, destination

    @staticmethod
    def _unzip_dir(workdir):
        extract_to = str(os.path.join(os.path.dirname(workdir), os.path.basename(workdir).split('.')[0]))
        if not os.path.exists(extract_to):
            os.makedirs(extract_to)
        with zipfile.ZipFile(workdir, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        return extract_to

    @staticmethod
    def _read_file(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Vault structure comparison')
    parser.add_argument('--workdir', type=str, required=True)
    args = parser.parse_args()
    VaultDiff(
        workdir=args.workdir
    )
