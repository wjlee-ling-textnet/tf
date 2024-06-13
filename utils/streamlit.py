import streamlit as st

from typing import Union, List
from PIL import Image, ImageDraw
from streamlit import session_state as sst
from streamlit_drawable_canvas import st_canvas


def make_button(label):
    return st.sidebar.button(label, disabled=(label not in st.session_state.next_steps))


def update_phase(new_phase):
    sst.phase = new_phase


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


def add_table(column):
    with column:
        canvas_result = adjust_box(sst.im, key="new_table_canvas")
        if canvas_result.json_data is not None and len(
            canvas_result.json_data["objects"]
        ):
            new_box = canvas_result.json_data["objects"][0]
            new_box = (
                new_box["left"],
                new_box["top"],
                new_box["left"] + new_box["width"],
                new_box["top"] + new_box["height"],
            )
            if new_box not in st.session_state.table_bboxes:
                st.session_state.table_bboxes.append(new_box)
            st.sidebar.info(st.session_state.table_bboxes[-1])


def adjust_box(_page_image, box=None, **kwargs):
    im_pil = _page_image.original.convert("RGB")
    canvas_image = Image.new("RGB", im_pil.size, (255, 255, 255))
    canvas_image.paste(im_pil)
    _kwargs = {
        "fill_color": "rgba(255, 165, 0, 0.3)",
        "stroke_width": 2,
        "stroke_color": "green",
        "background_image": canvas_image,
        "update_streamlit": True,
        "height": im_pil.height,
        "width": im_pil.width,
        "drawing_mode": "rect",
        "key": "canvas",
    }

    if box is not None:
        _kwargs["initial_drawing"] = {
            "shapes": [
                {
                    "type": "rect",
                    "x1": box[0],
                    "y1": box[1],
                    "x2": box[2],
                    "y2": box[3],
                    "lineWidth": 2,
                    "strokeStyle": "red",
                }
            ]
        }
    if "key" in kwargs:
        _kwargs["key"] = kwargs["key"]
    canvas_result = st_canvas(**_kwargs)
    return canvas_result
