import streamlit as st
import pandas as pd
from ..api.keboola_api import validate_token
from ..utils.session_state import update_project


def format_branch_options(branches):
    """Format branch options with default branch first."""
    default_branch = None
    other_branches = []

    for branch in branches:
        if branch['isDefault']:
            default_branch = (branch['name'], '(default)', branch['id'])
        else:
            other_branches.append((branch['name'], '', branch['id']))

    other_branches.sort(key=lambda x: x[0])
    return [default_branch] + other_branches if default_branch else other_branches


def validate_and_display_project(env_name: str, token: str):
    """Validate token and display project details."""
    with st.spinner(f'Validating token for {env_name}...'):
        validation_result = validate_token(st.session_state['stack'], token)
        if validation_result:
            project_id, kbc_project_name, project_url, project_branches = validation_result

            with st.success(f"""
                **Project Details:**
                - ID: {project_id}
                - Name: {kbc_project_name}
                - Link: {project_url}
            """):
                pass

            if project_branches:
                branch_names = format_branch_options(project_branches)
                return {
                    'project_id': project_id,
                    'kbc_project_name': kbc_project_name,
                    'project_url': project_url,
                    'branch_names': branch_names,
                    'branches': project_branches
                }
    return None


@st.dialog('Add a new project', width='large')
def add_project_dialog():
    """Dialog for adding a new project."""
    if 'environments' not in st.session_state or st.session_state['environments'].empty:
        st.info("Please setup environments first")
        return
    if 'stack' not in st.session_state:
        st.info("Please select a stack first")
        return

    env_names = st.session_state['environments']['env_name'].unique()
    project_name = st.text_input('Project Name',
                                 help='Create a name for the project group will be used as folders in VCS for your Keboola project sources')  # noqa

    tokens = {}
    validated_projects = {}
    selected_branches = {}
    all_fields_valid = True

    for env_name in env_names:
        st.subheader(f'{env_name}',help='Your defined environment')
        tokens[env_name] = st.text_input(f'Token', key=f'token_{env_name}', help='Keboola Storage token: https://help.keboola.com/management/project/tokens/#refreshing-token') # noqa

        if not tokens[env_name]:
            all_fields_valid = False
            continue

        project_details = validate_and_display_project(env_name, tokens[env_name])

        if project_details:
            validated_projects[env_name] = project_details
            branch_names = project_details['branch_names']

            selected_branch = st.selectbox(
                f'Select branch for {env_name}',
                options=branch_names,
                index=0,
                key=f'branch_{env_name}',
                format_func=lambda x: f"{x[0]}{x[1]}",
                disabled=True
            )
            selected_branches[env_name] = selected_branch
        else:
            all_fields_valid = False

    if all_fields_valid and project_name and len(selected_branches) == len(env_names):
        if st.button('Add Project'):
            new_row = {'project_name': project_name}
            for env_name in env_names:
                project_data = validated_projects[env_name]
                new_row[f'{env_name}_token'] = tokens[env_name]
                new_row[f'{env_name}_projectId'] = str(project_data['project_id'])
                new_row[f'{env_name}_kbc_project_name'] = project_data['kbc_project_name']
                new_row[f'{env_name}_url'] = project_data['project_url']

                branch_name, _, branch_id = selected_branches[env_name]
                new_row[f'{env_name}_branch'] = branch_name
                new_row[f'{env_name}_branchId'] = str(branch_id)

            update_project(new_row)
            st.rerun()
    else:
        if not project_name:
            st.warning('Please fill in the project name')
        elif not all_fields_valid:
            st.warning('Please ensure all tokens are valid')
        elif len(selected_branches) != len(env_names):
            st.warning('Please select branches for all environments')


@st.dialog('Edit project', width='large')
def edit_project_dialog():
    if st.session_state['project_mapping'].empty:
        st.info("No projects to edit")
        return

    project_name_to_edit = st.selectbox(
        'Select Project to Edit',
        options=st.session_state['project_mapping']['project_name'].tolist()
    )

    st.divider()    

    if project_name_to_edit:
        project_data = st.session_state['project_mapping'][
            st.session_state['project_mapping']['project_name'] == project_name_to_edit
            ].iloc[0]

        new_project_name = st.text_input(
            'New Project Name',
            value=project_name_to_edit,
            help='Update the name of this project'
        )

        env_names = st.session_state['environments']['env_name'].unique()
        tokens = {}
        validated_projects = {}
        selected_branches = {}
        all_fields_valid = True

        for env_name in env_names:
            st.subheader(f'{env_name}')
            tokens[env_name] = st.text_input(
                f'Token',
                value=project_data.get(f'{env_name}_token', ''),
                key=f'edit_token_{env_name}'
            )
            st.caption('Keboola Storage token: https://help.keboola.com/management/project/tokens/#refreshing-token')

            if not tokens[env_name]:
                all_fields_valid = False
                continue

            project_details = validate_and_display_project(env_name, tokens[env_name])

            if project_details:
                validated_projects[env_name] = project_details
                branch_options = format_branch_options(project_details['branches'])

                current_branch_id = project_data.get(f'{env_name}_branchId', '0')
                current_index = 0
                for i, (_, _, branch_id) in enumerate(branch_options):
                    if str(branch_id) == current_branch_id:
                        current_index = i
                        break

                selected_branch = st.selectbox(
                    f'Select branch for {env_name}',
                    options=branch_options,
                    index=current_index,
                    key=f'edit_branch_{env_name}',
                    format_func=lambda x: f"{x[0]}{x[1]}",
                    disabled=True
                )
                selected_branches[env_name] = selected_branch
            else:
                all_fields_valid = False

        if all_fields_valid and len(selected_branches) == len(env_names):
            if st.button('Save Changes'):
                mask = st.session_state['project_mapping']['project_name'] == project_name_to_edit
                
                if new_project_name != project_name_to_edit:
                    st.session_state['project_mapping'].loc[mask, 'project_name'] = new_project_name

                for env_name in env_names:
                    project_data = validated_projects[env_name]
                    selected_branch = selected_branches[env_name]
                    branch_name, _, branch_id = selected_branch

                    st.session_state['project_mapping'].loc[mask, [
                        f'{env_name}_token',
                        f'{env_name}_projectId',
                        f'{env_name}_kbc_project_name',
                        f'{env_name}_url',
                        f'{env_name}_branch',
                        f'{env_name}_branchId'
                    ]] = [
                        tokens[env_name],
                        str(project_data['project_id']),
                        project_data['kbc_project_name'],
                        project_data['project_url'],
                        branch_name,
                        str(branch_id)
                    ]
                st.success(f'Project "{new_project_name}" updated successfully!')
                st.rerun()
        else:
            if not all_fields_valid:
                st.warning('Please ensure all tokens are valid')
            elif len(selected_branches) != len(env_names):
                st.warning('Please select branches for all environments')


@st.dialog('Delete project')
def delete_project_dialog():
    """Dialog for deleting a project."""
    if st.session_state['project_mapping'].empty:
        st.info("No projects to delete")
        return

    name_to_delete = st.selectbox(
        'Select Project to Delete',
        options=st.session_state['project_mapping']['project_name'].tolist()
    )

    if name_to_delete:
        st.warning(f"Are you sure you want to delete project '{name_to_delete}'?")
        if st.button('Delete Project'):
            st.session_state['project_mapping'] = st.session_state['project_mapping'][
                st.session_state['project_mapping']['project_name'] != name_to_delete
                ]
            st.success(f'Project "{name_to_delete}" deleted successfully!')
            st.rerun()
