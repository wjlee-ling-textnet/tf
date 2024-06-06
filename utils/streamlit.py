import streamlit as st


def make_button(label, next_steps: list = None):
    if next_steps is not None:
        return st.sidebar.button(label, disabled=(label not in next_steps))
    else:
        return st.sidebar.button(label)
