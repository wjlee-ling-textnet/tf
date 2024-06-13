from parsers.images import extract_images_per_page, load_image_bboxes_per_page
from parsers.tables import (
    edit_table_contents,
    extract_table_coordinates_per_page,
    export_to_markdown,
    load_table_coordinates_per_page,
)
from utils.streamlit import (
    draw_boxes,
    add_table,
    update_phase,
    update_edit_idx,
    adjust_bbox,
)

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
    sst.table_bboxes = None
    sst.image_bboxes = None
    sst.plaintext_boxes = []
    sst.edit_idx = None
    sst.phase = None
    sst.df = None
    sst.tabula_df = None


st.set_page_config(layout="wide")
st.title("PDF-Markdown Converter")
with st.expander(
    label=f"status: {sst.phase if 'phase' in sst and sst.phase is not None else ''}"
):
    status_placeholder = st.empty()
preview_col, workspace_col = st.columns([0.5, 0.5])
preview_col = preview_col.empty()
# if "add_canvas" not in sst and "adjust_canvas" not in sst:
#     # 무한 캔버스 로딩 문제 해결
#     workspace_col = workspace_col.empty()

## 1단계: 전체 이미지/테이블 추출 & 저장
if "pdf" not in sst:
    sst.uploaded_file = st.file_uploader("Choose a PDF file to work on", type="pdf")
    if sst.uploaded_file:
        sst.pdf = pdfplumber.open(sst.uploaded_file)
        sst.root_dir = Path(
            os.path.join(
                os.path.expanduser("~"),
                "Downloads",
                sst.uploaded_file.name.replace(" ", "_").rstrip(".pdf"),
            )
        )
        sst.phase = None
        sst.page_idx = 0
        sst.edit_idx = None
        sst.image_bboxes = None
        sst.table_bboxes = None
        sst.df = None
        sst.tabula_df = None

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

    if sst.image_bboxes is None and sst.table_bboxes is None:
        sst.image_bboxes = load_image_bboxes_per_page(
            sst.page_idx + 1, sst.root_dir / "images"
        )

        sst.table_bboxes = load_table_coordinates_per_page(
            sst.page_idx + 1, sst.root_dir / "tables"
        )

    if "page_preview" not in sst or sst.page_preview is None:
        sst.page_preview = draw_boxes(
            im.original,
            sst.image_bboxes + sst.table_bboxes,
            colors=["green"] * len(sst.image_bboxes) + ["blue"] * len(sst.table_bboxes),
        )

    with preview_col:
        ## TODO: draw_boxes에 편입
        st.image(sst.page_preview, use_column_width=True)

    with workspace_col:
        if sst.phase in ["테이블 추가", "테이블 범위 수정"]:
            im_pil = im.original.convert("RGB")
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
            canvas_result = st_canvas(**_kwargs)

        elif sst.phase == "테이블 내용 수정" and sst.df is not None:
            new_dfs, code = spreadsheet(sst.df, sst.tabula_df)

    if (
        st.sidebar.button("테이블 추가", on_click=update_phase, args=("테이블 추가",))
        or sst.phase == "테이블 추가"
    ):
        # add_table(workspace_col, im)
        add_table(canvas_result)

    if len(sst.image_bboxes + sst.table_bboxes) > 0:
        element_to_edit = st.sidebar.selectbox(
            "요소 selectbox",
            sst.image_bboxes + sst.table_bboxes,
            key="element_to_edit",
            index=sst.edit_idx,
            on_change=update_edit_idx,
            args=(im.original,),
        )
        status_placeholder.write(element_to_edit)
        if element_to_edit:
            if (
                st.sidebar.button(
                    "테이블 범위 수정",
                    on_click=update_phase,
                    args=("테이블 범위 수정",),
                )
                or sst.phase == "테이블 범위 수정"
            ):
                # adjust_bbox(workspace_col, im)
                adjust_bbox(canvas_result)

            if (
                st.sidebar.button(
                    "테이블 내용 수정",
                    on_click=update_phase,
                    args=("테이블 내용 수정",),
                )
                or sst.phase == "테이블 내용 수정"
            ):
                edit_table_contents(page)

                if "md_df_name" not in sst:
                    sst.md_df_idx = None

                if st.sidebar.selectbox(
                    label="마크다운 변환할 데이터프레임 선택",
                    options=map(lambda num: f"df{str(num+1)}", range(len(new_dfs))),
                    index=None,
                    key="md_candidate_name",
                    on_change=export_to_markdown,
                    args=(new_dfs,),
                ):
                    st.rerun()

            if (
                st.sidebar.button(
                    "요소 삭제", on_click=update_phase, args=("요소 삭제",)
                )
                or sst.phase == "요소 삭제"
            ):
                if element_to_edit in sst.image_bboxes:
                    sst.image_bboxes.remove(element_to_edit)
                else:
                    sst.table_bboxes.remove(element_to_edit)

                sst.edit_idx = None
                sst.phase = None
