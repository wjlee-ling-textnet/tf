import streamlit as st

from typing import Union, List
from PIL import Image, ImageDraw


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


@st.cache_data
def draw_boxes(image, boxes: List, colors: Union[str, List[str]] = "blue"):
    if type(colors) == str:
        colors = [colors] * len(boxes)

    if boxes is not None:
        draw = ImageDraw.Draw(image)
        for box, color in zip(boxes, colors):
            draw.rectangle(box[:4], outline=color, width=2)
    return image
