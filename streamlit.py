import streamlit as st


def manage_inputs(input_type):
    # Kontrola, zda jsou potřeba upravit počty inputů
    current_count = st.session_state.get(f'{input_type}_count', 0)
    empty_inputs = [key for key in range(1, current_count + 1) if not st.session_state[f'{input_type}_{key}'].strip()]

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
        st.text_input("", key=f'{input_type}_{i}', on_change=manage_inputs, args=(input_type,))


def data():
    data = {
        "projects": [],
        "environments": []
    }
    project_count = st.session_state.get('projects_count', 0)
    environment_count = st.session_state.get('environments_count', 0)
    for i in range(1, project_count + 1):
        if st.session_state[f'projects_{i}'].strip():
            data["projects"].append(st.session_state[f'projects_{i}'])

    for i in range(1, environment_count + 1):
        if st.session_state[f'environments_{i}'].strip():
            data["environments"].append(st.session_state[f'environments_{i}'])

    return data


# Display Environments inputs in the first column and Projects inputs in the second column
display_inputs('environments', 'Enter environments')
display_inputs('projects', 'Enter projects')


