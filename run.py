import streamlit as st
from pathlib import Path
import base64

from src.workflow_generator.workflows import WorkflowGenerator, GITHUB_KEY

root_path = Path(__file__).parent

logo_image = base64.b64encode(open(f"{root_path}/src/images/keboola.png", "rb").read()).decode()
logo_html = f"""<div style="display: flex; justify-content: flex-end;"><img src="data:image/png;base64,
{logo_image}" style="width: 100px; margin-left: -10px;"></div>"""


def manage_inputs(input_type):
    # Kontrola, zda jsou potřeba upravit počty inputů
    current_count = st.session_state.get(f'{input_type}_count', 0)
    empty_inputs = [key for key in range(1, current_count + 1) if
                    not st.session_state[f'{input_type}_{key}'].strip()]

    # Odebrání přebytečných prázdných polí, kromě jednoho
    while len(empty_inputs) > 1:
        empty_key = empty_inputs.pop()
        st.session_state.pop(f'{input_type}_{empty_key}', None)
        st.session_state[f'{input_type}_count'] -= 1
        # Aktualizace klíčů zbylých polí
        for i in range(empty_key, st.session_state[f'{input_type}_count'] + 1):
            st.session_state[f'{input_type}_{i}'] = st.session_state.pop(f'{input_type}_{i + 1}')

    # Přidání nového prázdného pole, pokud neexistuje žádné prázdné
    if not empty_inputs and current_count > 0:
        new_input_key = f'{input_type}_{current_count + 1}'
        st.session_state[new_input_key] = ""
        st.session_state[f'{input_type}_count'] = current_count + 1


def display_inputs(input_type, title):
    # Vytvoření nadpisu a vstupních polí ve sloupci
    st.markdown(f"####")
    st.markdown(f"{title}")
    current_count = st.session_state.get(f'{input_type}_count', 0)
    if current_count == 0:
        st.session_state[f'{input_type}_count'] = 1
        st.session_state[f'{input_type}_1'] = ""
        current_count = 1
    for i in range(1, current_count + 1):
        st.text_input(f'{input_type}_{i}', label_visibility='hidden', key=f'{input_type}_{i}', on_change=manage_inputs,
                      args=(input_type,))


def data():
    project_count = st.session_state.get('projects_count', 0)
    projects = []
    for i in range(1, project_count + 1):
        if st.session_state[f'projects_{i}'].strip():
            projects.append(st.session_state[f'projects_{i}'])

    environment_count = st.session_state.get('environments_count', 0)
    environments = []
    for i in range(1, environment_count + 1):
        if st.session_state[f'environments_{i}'].strip():
            environments.append(st.session_state[f'environments_{i}'])

    return projects, environments


def main():
    st.markdown(f"{logo_html}", unsafe_allow_html=True)
    st.title("Creating CI/CD workflow for Keboola Connection CLI")

    platform = st.selectbox("Select SCM platform", [GITHUB_KEY])

    # Display Environments inputs in the first column and Projects inputs in the second column
    display_inputs('environments', 'Enter environments')
    display_inputs('projects', 'Enter projects')

    if st.button("Generate workflows"):
        projects, environments = data()
        if len(projects) == 0 or len(environments) == 0:
            st.warning("Please enter at least one project and one environment")
            return

        generator = WorkflowGenerator(str(root_path), platform, environments, projects)

        st.markdown("---")
        zip_path, zip_file_name = generator.get_zip_file()

        with open(zip_path, "rb") as file:
            st.download_button(
                label=f"Download {platform} CI/CD workflow",
                data=file,
                file_name=zip_file_name,
                mime="application/zip"
            )
        st.markdown(f"## Setup Instructions ({platform}):")
        st.markdown(generator.get_manual())


if __name__ == "__main__":
    main()
