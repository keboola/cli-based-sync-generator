# base.py
from typing import List
import os
import shutil
import jinja2
import zipfile


class WorkflowTemplate:
    template_dir: str
    template_file: str
    template_output_dir: str
    filled_file: str

    def __init__(self, template_dir, template_file, template_output_dir, filled_file):
        self.template_dir = template_dir
        self.template_file = template_file
        self.template_output_dir = template_output_dir
        self.filled_file = filled_file


class WorkflowGeneratorBase:
    _root_path: str
    _generated_files = []
    _templates: List[WorkflowTemplate]
    _template_data = {}
    _zip_output_folder: str
    _zip_file_name: str

    def __init__(self, root_path, template_data: {}, list_of_templates: List[WorkflowTemplate]):
        self._root_path = root_path
        self._templates = list_of_templates
        self._template_data = template_data

    def get_zip(self, output_folder: str, zip_file_name: str):
        # This method should be overridden by subclasses to provide final output folder in zip
        raise NotImplementedError

    def get_manual(self):
        # This method should be overridden by subclasses to provide final output folder in zip
        raise NotImplementedError

    def _render_template(self, template: WorkflowTemplate):
        if os.path.exists(template.template_output_dir):
            shutil.rmtree(template.template_output_dir)
        output_file_path = f"{template.template_output_dir}/{template.filled_file}"
        # Setup Jinja environment and load template
        template_loader = jinja2.FileSystemLoader(searchpath=template.template_dir)
        template_env = jinja2.Environment(loader=template_loader)
        template_jinja = template_env.get_template(template.template_file)

        # Render the template with data
        output = template_jinja.render(self._template_data)

        # Save the rendered template to a file
        with open(output_file_path, 'w') as f:
            f.write(output)

        print(f"Generated {output_file_path} successfully.")
        return output_file_path

    def _generate(self):
        for template in self._templates:
            self._generated_files.append(self._render_template(template))
        return self._generated_files

    def _create_zip_file(self, paths_to_zip: List[str], zip_output_folder, zip_file_name):
        self._zip_file_name = zip_file_name
        self._zip_output_folder = zip_output_folder
        if not os.path.exists(self._zip_output_folder):
            os.makedirs(self._zip_output_folder)

        zip_file_path = os.path.join(self._zip_output_folder, self._zip_file_name)
        print(f"Creating zip file: {zip_file_path}")

        with zipfile.ZipFile(zip_file_path, mode="w") as zf:
            for path in paths_to_zip:
                if os.path.isdir(path):
                    # Start the arcname from the base folder name
                    base_folder_name = os.path.basename(path.rstrip(os.sep))
                    for dir_name, sub_dirs, files in os.walk(path):
                        for filename in files:
                            file_path = os.path.join(dir_name, filename)
                            # Build the arcname with the base folder name included
                            arc_name = os.path.join(base_folder_name, os.path.relpath(file_path, start=path))
                            zf.write(file_path, arc_name, compress_type=zipfile.ZIP_DEFLATED)
                elif os.path.isfile(path):
                    base_folder_name = os.path.basename(os.path.dirname(path))
                    arc_name = os.path.join(base_folder_name, os.path.basename(path))
                    zf.write(path, arc_name, compress_type=zipfile.ZIP_DEFLATED)
                else:
                    print(f"Path {path} not found.")
        print(f"Zip file {zip_file_path} was created.")
        return zip_file_path, self._zip_file_name
