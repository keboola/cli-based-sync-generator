import streamlit as st
from streamlit_tags import st_tags
import base64

from src.workflow_generator.workflows import WorkflowGenerator, GITHUB_KEY

logo_image = base64.b64encode(open("src/images/keboola.png", "rb").read()).decode()
logo_html = f"""<div style="display: flex; justify-content: flex-end;"><img src="data:image/png;base64,{logo_image}" style="width: 100px; margin-left: -10px;"></div>"""


def main():
    st.markdown(f"{logo_html}", unsafe_allow_html=True)
    st.title("Creating Github Actions workflow form")

    platform = st.selectbox("Select SCM platform", [GITHUB_KEY])

    environments = st_tags(label='Enter environments:', key=f"env")
    projects = st_tags(label='Enter projects:', key=f"proj")

    if st.button("Generate workflows"):
        st.write("Generating workflows...")

        # Progress bar
        progress_bar = st.progress(0)

        generator = WorkflowGenerator(platform, environments, projects)
        progress_bar.progress(50)

        zip_path, zip_file_name = generator.get_zip_file()
        progress_bar.progress(100)

        st.write("Workflows generated!")

        st.markdown(generator.get_manual())

        with open(zip_path, "rb") as file:
            st.download_button(
                label="Download Zip file",
                data=file,
                file_name=zip_file_name,
                mime="application/zip"
            )


if __name__ == "__main__":
    main()
