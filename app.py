from parsers.images import extract_images_per_page

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


st.set_page_config(layout="wide")
st.title("PDF-Markdown Converter")
status_placeholder = st.empty()
col1, col2 = st.columns([0.4, 0.6])

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
        if not sst.root_dir.exists():
            sst.root_dir.mkdir(parents=True)

        with st.spinner("파일에서 이미지/테이블 추출 중"):
            for page in sst.pdf.pages:
                ## 이미지 추출 & 저장
                extract_images_per_page(page, output_dir=sst.root_dir / "images")
