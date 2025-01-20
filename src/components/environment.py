import streamlit as st
import pandas as pd
from ..utils.session_state import update_environment

@st.dialog('Add a new environment')
def add_environment_dialog():
    """Dialog for adding a new environment."""
    env_name = st.text_input('Environment Name', help='Name of the Git environment')
    branch = st.text_input('Branch', help='Branch name in the Git repository')

    if st.button('Add'):
        if env_name and branch:
            if env_name not in st.session_state['environments']['env_name'].values:
                update_environment({
                    "env_name": env_name,
                    "branch": branch
                })
                st.rerun()
            else:
                st.warning('Environment already exists')
        else:
            st.warning('Please fill all the fields')

@st.dialog('Edit environment')
def edit_environment_dialog():
    """Dialog for editing an environment."""
    if st.session_state['environments'].empty:
        st.info("No environments to edit")
        return

    name_to_edit = st.selectbox('Environment Name', 
                               st.session_state['environments']['env_name'].unique())

    if name_to_edit:
        selected_env = st.session_state['environments'][
            st.session_state['environments']['env_name'] == name_to_edit
        ].iloc[0]

        branch = st.text_input('Branch', value=selected_env['branch'])
        st.caption('Branch name in the Git repository')

        if st.button('Save Changes'):
            if branch:
                st.session_state['environments'].loc[
                    st.session_state['environments']['env_name'] == name_to_edit,
                    ['branch']
                ] = [branch]
                st.success(f'Environment "{name_to_edit}" updated successfully!')
                st.rerun()
            else:
                st.warning('Please fill all the fields')

@st.dialog('Delete environment')
def delete_environment_dialog():
    """Dialog for deleting an environment."""
    if st.session_state['environments'].empty:
        st.info("No environments to delete")
        return

    name_to_delete = st.selectbox('Environment Name', 
                                 st.session_state['environments']['env_name'].unique())

    if st.button('Delete'):
        if name_to_delete in st.session_state['environments']['env_name'].values:
            # Remove environment columns from project mapping
            columns_to_drop = [col for col in st.session_state['project_mapping'].columns 
                             if col.startswith(f'{name_to_delete}_')]
            st.session_state['project_mapping'] = st.session_state['project_mapping'].drop(
                columns=columns_to_drop, 
                errors='ignore'
            )
            
            # Remove environment from environments
            st.session_state['environments'] = st.session_state['environments'][
                st.session_state['environments']['env_name'] != name_to_delete
            ]
            st.rerun()
