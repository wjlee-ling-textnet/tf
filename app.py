from parsers.images import extract_images_per_page, load_image_bboxes_per_page
from parsers.tables import (
    extract_table_coordinates_per_page,
    load_table_coordinates_per_page,
)
from utils.streamlit import draw_boxes, add_table, update_phase, update_edit_idx

import os
import pdfplumber
import tabula
import streamlit as st

from mitosheet.streamlit.v1 import spreadsheet
from pathlib import Path
from PIL import Image, ImageDraw
from streamlit import session_state as sst
from streamlit_drawable_canvas import st_canvas
from streamlit_quill import st_quill
from typing import Union, List


def _turn_page():
    if "markdown" in sst:
        # 2단계 활성화
        del sst["markdown"]

    sst.page_idx = sst.user_input_page_idx - 1
    sst.page_preview = None
    sst.table_boxes = []
    sst.image_boxes = []
    sst.plaintext_boxes = []
    sst.edit_idx = None
    sst.phase = None


st.set_page_config(layout="wide")
st.title("PDF-Markdown Converter")
status_placeholder = st.empty()
preview_col, workspace_col = st.columns([0.5, 0.5])
preview_col = preview_col.empty()
# workspace_col = workspace_col.empty()

## 1단계: 전체 이미지/테이블 추출 & 저장
if "pdf" not in sst:
    uploaded_file = st.file_uploader("Choose a PDF file to work on", type="pdf")
    if uploaded_file:
        sst.pdf = pdfplumber.open(uploaded_file)
        sst.root_dir = Path(
            os.path.join(
                os.path.expanduser("~"),
                "Downloads",
                uploaded_file.name.replace(" ", "_").rstrip(".pdf"),
            )
        )
        sst.phase = None
        sst.page_idx = 0
        sst.edit_idx = None

        if not sst.root_dir.exists():
            sst.root_dir.mkdir(parents=True)

        with st.spinner("파일에서 이미지/테이블 추출 중"):
            for page in sst.pdf.pages:
                ## 이미지 추출 & 저장
                extract_images_per_page(page, output_dir=sst.root_dir / "images")

                ## 테이블 좌표 추출 & 저장
                extract_table_coordinates_per_page(page, sst.root_dir / "tables")

        st.rerun()

## 2단계: 이미지/테이블 수정 및 검수. 페이지 마크다운 생성 전
elif "markdown" not in sst:
    st.sidebar.number_input(
        "작업 페이지 번호",
        min_value=1,
        max_value=len(sst.pdf.pages),
        value=1,
        on_change=_turn_page,
        key="user_input_page_idx",
    )

    page = sst.pdf.pages[sst.page_idx]
    im = page.to_image()

    sst.image_bboxes = load_image_bboxes_per_page(
        sst.page_idx + 1, sst.root_dir / "images"
    )

    sst.table_bboxes = load_table_coordinates_per_page(
        sst.page_idx + 1, sst.root_dir / "tables"
    )
    if sst.phase not in ["요소 selectbox"]:
        sst.page_preview = draw_boxes(
            im.original,
            sst.image_bboxes + sst.table_bboxes,
            colors=["green"] * len(sst.image_bboxes) + ["blue"] * len(sst.table_bboxes),
        )

    with preview_col:
        st.image(sst.page_preview, use_column_width=True)

    if (
        sst.table_bboxes
        and st.sidebar.button(
            "테이블 추가", on_click=update_phase, args=("테이블 추가",)
        )
    ) or sst.phase == "테이블 추가":
        with workspace_col:
            add_table(workspace_col, im)

    if len(sst.table_bboxes + sst.image_bboxes) > 0:
        element_to_edit = st.sidebar.selectbox(
            "Select Table to Edit",
            st.session_state.table_bboxes,
            key="element_to_edit",
            index=sst.edit_idx,
            on_change=update_edit_idx,
            args=(im.original,),
        )

        if element_to_edit:
            st.warning(element_to_edit)
