import streamlit as st
from ..constants import DEFAULT_STACKS

def stack_dialog():
    """Dialog for selecting or entering a custom Keboola stack."""
    st.subheader("Keboola Stack", help="Select or enter the Keboola stack (https://help.keboola.com/overview/#stacks)")
    
    # Radio button for selecting between predefined and custom stacks
    stack_type = st.radio(
        "Select stack type",
        ["Predefined Stack", "Custom Stack"],
        horizontal=True
    )
    
    selected_stack = None
    
    if stack_type == "Predefined Stack":
        selected_stack = st.selectbox(
            "Select Keboola Stack",
            options=DEFAULT_STACKS,
            help="Choose from predefined Keboola stacks"
        )
    else:
        selected_stack = st.text_input(
            "Enter Custom Stack URL",
            help="Enter the full URL of your Keboola stack (e.g., https://connection.custom.keboola.com)",
            placeholder="https://connection.custom.keboola.com"
        )
    
    return selected_stack 