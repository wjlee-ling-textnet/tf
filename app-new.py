from parsers.image_extract import extract_images_pdfplumber
from parsers.pdf import get_plaintext_boxes_pdfplumber, get_plaintext_boxes_as_string
from utils.streamlit import make_button

import pdfplumber
import tabula
import pandas as pd
import streamlit as st

from typing import Union, List
from PIL import Image, ImageDraw
from streamlit_drawable_canvas import st_canvas
from mitosheet.streamlit.v1 import spreadsheet


if "table_boxes" not in st.session_state:
    st.session_state.page_idx = 0
    st.session_state.page_preview = None
    st.session_state.table_boxes = []
    st.session_state.image_boxes = []
    st.session_state.plaintext_boxes = []
    st.session_state.table_to_edit_idx = None
    st.session_state.next_steps = ["모든 테이블 인식", "이미지 추출", "텍스트 추출"]
    st.session_state.df = None
    st.session_state.save_df_idx = None


def turn_page():
    st.session_state.page_idx = st.session_state.user_input_page_idx - 1
    st.session_state.page_preview = None
    st.session_state.table_boxes = []
    st.session_state.image_boxes = []
    st.session_state.plaintext_boxes = []
    st.session_state.table_to_edit_idx = None
    st.session_state.df = None
    st.session_state.save_df_idx = None
    st.session_state.next_steps = ["모든 테이블 인식", "이미지 추출", "텍스트 추출"]


def draw_boxes(image, boxes: List, colors: Union[str, List[str]] = "blue"):
    if type(colors) == str:
        colors = [colors] * len(boxes)

    if boxes is not None:
        draw = ImageDraw.Draw(image)
        for box, color in zip(boxes, colors):
            draw.rectangle(box, outline=color, width=2)
    return image


def adjust_box(_page_image, box=None):
    im_pil = _page_image.original.convert("RGB")
    canvas_image = Image.new("RGB", im_pil.size, (255, 255, 255))
    canvas_image.paste(im_pil)
    kwargs = {
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
        kwargs["initial_drawing"] = {
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
    canvas_result = st_canvas(**kwargs)
    return canvas_result


def update_table_to_edit_idx():
    if (
        "table_to_edit" in st.session_state
        and st.session_state.table_to_edit is not None
    ):
        st.session_state["table_to_edit_idx"] = st.session_state.table_boxes.index(
            st.session_state.table_to_edit
        )
        st.session_state.next_steps = ["테이블 범위 수정", "테이블 추출"]


def extract_table_content(bbox, padding=5):
    """bbox가 너무 타이트하면 바깥쪽 셀 내용은 추출 못함"""
    # 🍎 page 범위 내로 패딩
    extended_bbox = (
        bbox[0] - padding,
        bbox[1] - padding,
        bbox[2] + padding,
        bbox[3] + padding,
    )
    cropped_page = page.within_bbox(extended_bbox)
    new_table = cropped_page.extract_table()
    return new_table


def export_to_csv(new_dfs):
    if st.session_state.save_df_idx:
        st.sidebar.download_button(
            "Download CSV",
            new_dfs[st.session_state.save_df_idx].to_csv(index=False),
            file_name=f"page{st.session_state.page_idx+1}_{st.session_state.table_to_edit_idx+1}.csv",
        )


st.set_page_config(layout="wide")

st.title("PDF Table Edge Detection Adjustment")
col1, col2 = st.columns([0.4, 0.6])

uploaded_file = st.file_uploader(
    "Choose a PDF file", type="pdf", disabled=("pdf" in st.session_state)
)
if uploaded_file:
    st.session_state.pdf = pdfplumber.open(uploaded_file)

if "pdf" in st.session_state:
    st.sidebar.title("Adjust Table Edges")

    page_idx = st.sidebar.number_input(
        "페이지 쪽수",
        min_value=1,
        max_value=len(st.session_state.pdf.pages),
        value=1,
        on_change=turn_page,
        key="user_input_page_idx",
    )

    page = st.session_state.pdf.pages[st.session_state.page_idx]
    im = page.to_image()

    if st.session_state.page_preview is None:
        # if the user inputs a new page idx, update the page preview accordingly
        st.session_state.page_preview = im.original

    with col1:
        st.image(
            st.session_state.page_preview,
            caption=f"page {st.session_state.page_idx + 1}",
            use_column_width=True,
        )
    ## image 추출
    if st.session_state.image_boxes == []:
        if make_button("이미지 추출"):
            st.session_state.image_boxes = extract_images_pdfplumber(page)

    ## table 추출
    if st.session_state.table_boxes == []:
        if make_button("모든 테이블 인식"):
            detected_tables = page.find_tables()
            if detected_tables:
                st.session_state.table_boxes = [
                    (table.bbox) for table in detected_tables
                ]
                colors = ["blue"] * len(st.session_state.table_boxes)
                if st.session_state.table_to_edit_idx is not None:
                    colors[st.session_state.table_to_edit_idx] = "red"
                st.session_state.page_preview = draw_boxes(
                    im.original,
                    st.session_state.table_boxes,
                    colors=colors,
                )
                st.session_state.next_steps = ["모든 테이블 인식", "테이블 csv 추출"]
                st.rerun()

            else:
                if st.sidebar.button(
                    "테이블 범위 설정",
                    on_click=lambda: st.session_state.next_steps.append(
                        "테이블 범위 설정"
                    ),
                ):
                    pass

        elif "테이블 범위 설정" in st.session_state.next_steps:
            with col2:
                canvas_result = adjust_box(
                    im,
                )
            if canvas_result.json_data is not None and len(
                canvas_result.json_data["objects"]
            ):
                st.session_state.table_to_edit_idx = 0
                new_box = canvas_result.json_data["objects"][0]
                st.session_state.table_boxes.append(
                    (
                        new_box["left"],
                        new_box["top"],
                        new_box["left"] + new_box["width"],
                        new_box["top"] + new_box["height"],
                    )
                )
                st.sidebar.info(
                    st.session_state.table_boxes[st.session_state.table_to_edit_idx]
                )
                st.session_state.next_steps = ["수정 완료"]
                st.rerun()

    else:
        table_to_edit = st.sidebar.radio(
            "Select Table to Edit",
            st.session_state.table_boxes,
            key="table_to_edit",
            index=st.session_state.table_to_edit_idx,
            on_change=update_table_to_edit_idx,
        )

        if table_to_edit:
            if (
                make_button("테이블 범위 수정")
                or "canvas" in st.session_state
                # need this condition because the widget box is created after running 'adjust_box' more than two times
            ):
                with col2:
                    canvas_result = adjust_box(
                        im,
                        st.session_state.table_boxes[
                            st.session_state.table_to_edit_idx
                        ],
                    )
                if canvas_result.json_data is not None and len(
                    canvas_result.json_data["objects"]
                ):
                    new_box = canvas_result.json_data["objects"][0]
                    st.session_state.table_boxes[st.session_state.table_to_edit_idx] = (
                        new_box["left"],
                        new_box["top"],
                        new_box["left"] + new_box["width"],
                        new_box["top"] + new_box["height"],
                    )
                    st.sidebar.info(
                        st.session_state.table_boxes[st.session_state.table_to_edit_idx]
                    )
                st.session_state.next_steps = ["수정 완료"]

            if make_button("수정 완료"):
                if "canvas" in st.session_state:
                    del st.session_state["canvas"]

                colors = ["blue"] * len(st.session_state.table_boxes)
                colors[st.session_state.table_to_edit_idx] = "green"
                st.session_state.page_preview = draw_boxes(
                    im.original,
                    st.session_state.table_boxes,
                    colors=colors,
                )
                st.session_state.next_steps = ["테이블 추출"]
                st.rerun()

            if make_button("테이블 추출") or st.session_state.df is not None:
                st.session_state.next_steps = [
                    "테이블 csv 저장",
                    "다른 방법으로 재추출",
                    "텍스트 추출",
                ]

                box = st.session_state.table_boxes[st.session_state.table_to_edit_idx]
                if st.session_state.df is None:
                    new_table = extract_table_content(
                        box,
                        padding=10,
                    )
                    st.session_state.df = pd.DataFrame(
                        new_table,
                        index=None,
                    )  ## 🍎🍎 TODO: no-index
                    st.session_state.tabula_df = tabula.read_pdf(
                        uploaded_file,
                        area=[box[1], box[0], box[3], box[2]],
                        pages=st.session_state.user_input_page_idx,
                        multiple_tables=False,
                        stream=True,
                    )[0]
                with col2:
                    new_dfs, code = spreadsheet(
                        st.session_state.df, st.session_state.tabula_df
                    )
                if make_button("테이블 csv 저장") or st.session_state.save_df_idx:
                    st.sidebar.selectbox(
                        label="Select a DataFrame to export",
                        options=map(lambda num: f"df{str(num+1)}", range(len(new_dfs))),
                        index=None,
                        key="save_df_idx",
                    )
                    export_to_csv(new_dfs)
                    st.session_state.next_steps = ["테이블 수정 및 제거", "텍스트 추출"]

    if st.session_state.table_boxes:
        if make_button("텍스트 추출"):
            plaintext_boxes = page.extract_words(
                # layout=True,
                x_tolerance=2,
                extra_attrs=["fontname", "size"],
            )
            st.session_state.plaintext_boxes = get_plaintext_boxes_pdfplumber(
                plaintext_boxes, st.session_state.table_boxes
            )  ## TODO: table의 경우 마크다운으로 추출

            plaintext_boxes_str = get_plaintext_boxes_as_string(
                st.session_state.plaintext_boxes
            )
            st.warning(plaintext_boxes_str)
