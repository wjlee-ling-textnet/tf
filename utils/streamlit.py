import streamlit as st


def make_button(label):
    return st.sidebar.button(label, disabled=(label not in st.session_state.next_steps))


def choose_delete_false_positives(boxes: list[tuple]):
    """
    오인식된 이미지/테이블 박스를 선택해서 제거
    Returns:
        list: 선택된 오인식된 박스들
    """
    false_positives = st.sidebar.multiselect("오인식된 요소 선택", boxes, [])
    if false_positives:
        for pos in false_positives:
            boxes.remove(pos)

    return false_positives
