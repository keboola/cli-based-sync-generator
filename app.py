from pathlib import Path
import streamlit as st
import pandas as pd

from src.constants import LOGO_HTML, set_page_config
from src.utils.session_state import init_session_state
from src.components.environment import (
    add_environment_dialog,
    edit_environment_dialog,
    delete_environment_dialog
)
from src.components.project import (
    add_project_dialog,
    edit_project_dialog,
    delete_project_dialog
)
from src.components.stack import stack_dialog
from src.workflow_generator.workflows import WorkflowGenerator


def main():
    # Set page configuration
    set_page_config()

    # Set the logo and page title
    st.markdown(LOGO_HTML, unsafe_allow_html=True)

    # Initialize session state
    init_session_state()

    # Setup VCS
    st.markdown('---')
    st.subheader('Pipeline Actions (Version Control Setup)')
    scm_platform = st.selectbox('VCS Platform',
                                ['GitHub'],
                                key='scm_platform',
                                help="Choose your version control system where you want to set up the CI/CD pipeline")

    # Setup Environments
    st.markdown('---')
    st.subheader('Setup VCS Environments', help="Add, edit or delete environments to be used in the CI/CD pipeline")

    # Environment controls
    col1, col2, col3 = st.columns(3)
    if col1.button('➕ Add a new environment', use_container_width=True):
        add_environment_dialog()
    if col2.button('✎ Edit an environment', use_container_width=True):
        edit_environment_dialog()
    if col3.button('➖ Delete an environment', use_container_width=True):
        delete_environment_dialog()

    # Display environments
    st.dataframe(
        st.session_state['environments'],
        column_config={
            'env_name': 'Environment Name',
            'branch': 'Branch'
        },
        use_container_width=True,
        hide_index=True
    )

    # Stack Selection
    st.markdown('---')
    selected_stack = stack_dialog()
    if selected_stack:
        st.session_state['stack'] = selected_stack
    elif 'stack' not in st.session_state:
        st.warning("Please select or enter a Keboola stack to continue")
        return

    # Project Mapping
    st.markdown('---')
    st.subheader('Project Mapping', help="Map projects to environments for the CI/CD pipeline")

    # Project controls
    col1, col2, col3 = st.columns(3)
    if col1.button('➕ Add a new project', use_container_width=True):
        add_project_dialog()
    if col2.button('✎ Edit a project', use_container_width=True):
        edit_project_dialog()
    if col3.button('➖ Delete a project', use_container_width=True):
        delete_project_dialog()

    # Project table display
    df = pd.DataFrame(columns=['project_name']) if st.session_state['project_mapping'].empty else st.session_state[
        'project_mapping']

    # Basic column configuration
    columns = ['project_name']
    column_config = {
        'project_name': 'Project Name'
    }

    # Add columns for each environment
    if 'environments' in st.session_state and not st.session_state['environments'].empty:
        for env_name in st.session_state['environments']['env_name'].unique():
            # Add project name column
            project_col = f'{env_name}_project'
            columns.append(project_col)

            # Initialize project column if not exists
            if project_col not in df.columns:
                df[project_col] = None

            # Add project URL column
            url_col = f'{env_name}_url'
            columns.append(url_col)

            # Initialize URL column if not exists
            if url_col not in df.columns:
                df[url_col] = None

            if not df.empty:
                # Update project name column
                df[project_col] = df.apply(
                    lambda row: (
                        f"{row[f'{env_name}_kbc_project_name']} ({str(row[f'{env_name}_projectId']).split('.')[0]})"
                        if all(f'{env_name}_{key}' in row.index for key in ['kbc_project_name', 'projectId'])
                        else "⚠️ Configuration needed"
                    ),
                    axis=1
                )

                # Update URL column
                df[url_col] = df.apply(
                    lambda row: row[f'{env_name}_url'] if f'{env_name}_url' in row.index else None,
                    axis=1
                )

                # Update branchId from environment configuration
                branch_id_col = f'{env_name}_branchId'

                if not df.empty:
                    df[branch_id_col] = df.apply(
                        lambda row: row.get(f'{env_name}_branchId', '0'),  # Použijeme přímo uložené branchId
                        axis=1
                    )
                else:
                    df[branch_id_col] = '0'

            # Configure columns
            column_config[project_col] = st.column_config.TextColumn(
                f"Keboola Project ({env_name})",
                help=f"Project name and ID for {env_name} environment"
            )
            column_config[url_col] = st.column_config.LinkColumn(
                f"Keboola Project ({env_name}) Link",
                help=f"Project URL for {env_name} environment"
            )

    # Display the table
    st.dataframe(
        df[columns],
        column_config=column_config,
        use_container_width=True,
        hide_index=True
    )

    # Generate workflow
    st.divider()
    st.subheader('Generated CI/CD Workflow')

    if (len(st.session_state['project_mapping']) > 0 and
            len(st.session_state['environments']) > 0):

        generator = WorkflowGenerator(
            str(Path(__file__).parent),
            scm_platform,
            st.session_state['stack'],
            st.session_state['environments'].to_dict(orient='records'),
            st.session_state['project_mapping'].to_dict(orient='records')
        )

        st.session_state['zip_path'], st.session_state['zip_file_name'] = generator.get_zip_file()
        st.session_state['manual'] = generator.get_manual()

        if 'zip_path' in st.session_state and 'manual' in st.session_state:
            with open(st.session_state['zip_path'], "rb") as file:
                st.download_button(
                    label=f"Download {scm_platform} CI/CD workflow",
                    data=file,
                    file_name=st.session_state['zip_file_name'],
                    mime="application/zip"
                )
            st.markdown(f"# Setup Instructions ({scm_platform}):")
            st.markdown(st.session_state['manual'], unsafe_allow_html=True)


if __name__ == "__main__":
    main()
