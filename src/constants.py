import streamlit as st

# Default stacks
DEFAULT_STACKS = [
   'connection.keboola.com',
   'connection.us-east4.gcp.keboola.com',
   'connection.eu-central-1.keboola.com',
   'connection.north-europe.azure.keboola.com',
   'connection.europe-west3.gcp.keboola.com'
]

# Logo HTML
LOGO_HTML = """
<div style="text-align: center; padding: 1rem;">
    <div style="background-color: white; padding: 1rem; display: inline-block; border-radius: 5px;">
        <img src="https://assets-global.website-files.com/5e21dc6f4c5acf29c35bb32c/5e21e66410e34945f7f25add_Keboola_logo.svg" width="200" style="max-width: 100%; height: auto;">
    </div>
    <h1>Project Lifecycle Manager</h1>
</div>
"""

# Page configuration
def set_page_config():
    # Set page configuration
    st.set_page_config(
        page_title="Keboola CI/CD Generator",
        layout="centered"
    )

    # Custom CSS to increase content width but not to maximum
    st.markdown("""
        <style>
            .block-container {
                padding-top: 1rem;
                padding-bottom: 0rem;
                padding-left: 1rem;
                padding-right: 1rem;
                max-width: 1000px;
            }
            h1 {
                color: #033494;
                padding-top: 1rem;
            }
            img {
                object-fit: contain;
            }
        </style>
    """, unsafe_allow_html=True)
