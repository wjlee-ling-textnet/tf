import streamlit as st


def make_button(label):
    return st.sidebar.button(label, disabled=(label not in st.session_state.next_steps))
