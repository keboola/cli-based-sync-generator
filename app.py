from pathlib import Path

import streamlit as st
import pandas as pd
import re

from src.workflow_generator.workflows import WorkflowGenerator

PROJECT_ID_REGEX = r"https://.*keboola\..*/projects/(\d+)"

# Set the logo adn page title
LOGO_URL = 'https://assets-global.website-files.com/5e21dc6f4c5acf29c35bb32c/5e21e66410e34945f7f25add_Keboola_logo.svg'
LOGO_HTML = f'''
<div style="display: flex; align-items: center; justify-content: left; font-size: 35px; font-weight: 600;">
    <img src="{LOGO_URL}" style="height: 40px;">
    <span style="margin: 0 20px;">Project Lifecycle Manager</span>
</div>
'''
st.markdown(LOGO_HTML, unsafe_allow_html=True)

# Initialize the session state
if 'environments' not in st.session_state:
    st.session_state['environments'] = pd.DataFrame(columns=['env_name'])
if 'project_mapping' not in st.session_state:
    st.session_state['project_mapping'] = pd.DataFrame(columns=['stack', 'project_name'])

# Setup Environments
st.markdown('---')
st.subheader('Setup Environments')
''

st.divider()


# Add and delete environments
@st.experimental_dialog('Add a new environment', width='large')
def add_environment():
    env_name = st.text_input('Environment Name')
    stack = st.selectbox('Stack', ['connection.keboola.com',
                                   'connection.us-east4.gcp.keboola.com',
                                   'connection.eu-central-1.keboola.com',
                                   'connection.north-europe.azure.keboola.com',
                                   'connection.europe-west3.gcp.keboola.com]'])
    branch = st.text_input('Branch')
    st.caption('Branch name in the SCM repository')

    if st.button('Add'):
        if env_name and stack and branch:
            if env_name not in st.session_state['environments']['env_name'].values:
                new_row = pd.DataFrame({"env_name": [env_name], "stack": [stack], "branch": [branch]})
                st.session_state['environments'] = pd.concat([st.session_state['environments'], new_row],
                                                             ignore_index=True)
                st.session_state['project_mapping'][f'{env_name}_id'] = ''
                st.session_state['project_mapping'][f'{env_name}_link'] = ''
                st.rerun()
            else:
                st.warning('Environment already exists')
        else:
            st.warning('Please fill all the fields')


@st.experimental_dialog('Delete an environment', width='large')
def delete_environment():
    name_to_delete = st.selectbox('Environment Name', st.session_state['environments']['env_name'].unique())

    if st.button('Delete'):
        if name_to_delete in st.session_state['environments']['env_name'].values:
            st.session_state['environments'] = st.session_state['environments'][
                st.session_state['environments']['env_name'] != name_to_delete]
            st.session_state['project_mapping'].drop(columns=[f'{name_to_delete}_id', f'{name_to_delete}_link'],
                                                     inplace=True, errors='ignore')
            st.rerun()
        else:
            st.warning('Environment not found')


col1, col2 = st.columns(2)
if col1.button('➕ Add a new environment', use_container_width=True):
    add_environment()

if col2.button('➖ Delete an environment', use_container_width=True):
    delete_environment()

# Display the environments
st.dataframe(
    st.session_state['environments'],
    column_config={
        'env_name': 'Environment Name',
        'stack': 'Stack',
        'branch': 'Branch'
    },
    use_container_width=True,
    hide_index=True
)

# Project Mapping
st.markdown('''---''')
st.subheader('Project Mapping')
''


def _parse_project_id(in_str):
    match = re.search(PROJECT_ID_REGEX, in_str)
    return match.group(1) if match else ''


# Add and delete projects
@st.experimental_dialog('Add a new project', width='large')
def add_project():
    if 'environments' not in st.session_state or st.session_state['environments'].empty:
        st.info("Please setup environments first")
        return

    project_name = st.text_input('Project Name')
    st.caption('Using as folder name in the SCM repository')
    links = {}

    st.divider()

    for env_name in st.session_state['environments']['env_name'].unique():
        st.subheader(f'{env_name}')
        links[env_name] = st.text_input(f'link', key=f'link_{env_name}')
        st.caption(f'Link to the project should be in the format: https://connection.keboola.com/admin/projects/*')

    if st.button('Add'):
        if project_name:
            # check if links are filled and valid with stack
            if all(str(st.session_state['environments']['stack'][
                           st.session_state['environments']['env_name'] == env].values[0])
                   in link for env, link in links.items()):
                new_row = {'project_name': project_name}
                if all(_parse_project_id(link).isdigit() for link in links.values()):
                    for env_name in st.session_state['environments']['env_name'].unique():
                        env_data = st.session_state['environments'][
                            st.session_state['environments']['env_name'] == env_name]
                        new_row['stack'] = env_data['stack'].values[0]
                        new_row['branch'] = env_data['branch'].values[0]
                        new_row[f'{env_name}_link'] = links[env_name]
                        new_row[f'{env_name}_id'] = _parse_project_id(links[env_name])

                    new_row_df = pd.DataFrame([new_row])
                    st.session_state['project_mapping'] = pd.concat(
                        [st.session_state['project_mapping'], new_row_df], ignore_index=True)
                    st.rerun()
                else:
                    st.warning('Link not contains valid project id. Please fill the correct link')
            else:
                st.warning(f'Please fill the project link in the same stack as the environment stack')
        else:
            st.warning('Please fill the project name')


@st.experimental_dialog('Delete a project', width='large')
def delete_project():
    name_to_delete = st.selectbox('Project Name', st.session_state['project_mapping']['project_name'])

    if st.button('Delete'):
        if name_to_delete in st.session_state['project_mapping']['project_name'].values:
            st.session_state['project_mapping'] = st.session_state['project_mapping'][
                st.session_state['project_mapping']['project_name'] != name_to_delete]
            st.rerun()
        else:
            st.warning('Environment not found')


col1, col2 = st.columns(2)
if col1.button('➕ Add a new project', use_container_width=True):
    add_project()

if col2.button('➖ Delete a project', use_container_width=True):
    delete_project()

# Display the project mapping
column_config = {'project_name': 'Project Name'}
for env_name in st.session_state['environments']['env_name'].unique():
    column_config[f'{env_name}_link'] = st.column_config.LinkColumn(f'{env_name}', display_text=PROJECT_ID_REGEX)

st.dataframe(
    st.session_state['project_mapping'][[col for col in st.session_state['project_mapping'].columns if
                                         '_id' not in col and col not in ['stack', 'branch', 'environment']]],
    column_config=column_config,
    use_container_width=True,
    hide_index=True
)

# Pipeline Actions
st.divider()
st.subheader('Pipeline Actions (Version Control Setup)')
scm_platform = st.selectbox('SCM Platform', ['GitHub', 'GitLab', 'Bitbucket'], key='scm_platform')

# Generate the environment
if st.button('Generate Environment'):
    st.divider()

    root_path = Path(__file__).parent

    generator = WorkflowGenerator(str(root_path),
                                  scm_platform,
                                  st.session_state['environments'].to_dict(orient='records'),
                                  st.session_state['project_mapping'].to_dict(orient='records'))

    zip_path, zip_file_name = generator.get_zip_file()

    with open(zip_path, "rb") as file:
        st.download_button(
            label=f"Download {scm_platform} CI/CD workflow",
            data=file,
            file_name=zip_file_name,
            mime="application/zip"
        )
    st.markdown(f"## Setup Instructions ({scm_platform}):")
    st.markdown(generator.get_manual())
