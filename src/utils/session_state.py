import pandas as pd
import streamlit as st
from typing import Dict, Any

def init_session_state():
    """Initialize session state variables."""
    if 'environments' not in st.session_state:
        st.session_state['environments'] = pd.DataFrame(columns=['env_name', 'branch'])
    
    if 'project_mapping' not in st.session_state:
        st.session_state['project_mapping'] = pd.DataFrame()

def update_environment(env_data: dict):
    """Update environment data in session state."""
    new_env = pd.DataFrame([{
        'env_name': env_data['env_name'],
        'branch': env_data['branch']
    }])
    
    if st.session_state['environments'].empty:
        st.session_state['environments'] = new_env
    else:
        st.session_state['environments'] = pd.concat(
            [st.session_state['environments'], new_env],
            ignore_index=True
        )

def update_project(project_data: Dict[str, Any]):
    """Update project data in session state."""
    new_row = pd.DataFrame([project_data])
    st.session_state['project_mapping'] = pd.concat(
        [st.session_state['project_mapping'], new_row],
        ignore_index=True
    )
