import streamlit as st
import pdfplumber
import tabula
import pandas as pd

from typing import Union, List
from PIL import Image, ImageDraw
from streamlit import experimental_rerun
from streamlit_drawable_canvas import st_canvas

if "table_boxes" not in st.session_state:
    st.session_state.table_boxes = None
    st.session_state.table_changes = None
    st.session_state.table_to_edit_idx = None
    st.session_state.page_idx = 0
    st.session_state.next_steps = []
    st.session_state.df = None


def draw_boxes(image, boxes: List, colors: Union[str, List[str]] = "blue"):
    if type(colors) == str:
        colors = [colors] * len(boxes)

    if boxes is not None:
        draw = ImageDraw.Draw(image)
        for box, color in zip(boxes, colors):
            draw.rectangle(box, outline=color, width=2)
    return image


def adjust_box(_page_image, box=None):
    print("🩷", "adjust_box")
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
        print("🩷", "updated table_to_edit_idx to ", st.session_state.table_to_edit_idx)
        st.session_state.next_steps.extend(["테이블 범위 수정", "테이블 추출"])


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


def export_to_csv(page_idx, table_idx):
    pass


# def adjust_replace_box(page_image):
#     st.session_state["table_to_edit_idx"] = st.session_state.table_boxes.index(
#         st.session_state.table_to_edit
#     )
#     # canvas로 수정
#     canvas_result = adjust_box(
#         page_image,
#         st.session_state.table_boxes[st.session_state.table_to_edit_idx],
#     )
#     if canvas_result.json_data["objects"]:
#         new_box = canvas_result.json_data["objects"][0]
#         st.session_state.table_boxes[st.session_state.table_to_edit_idx] = (
#             new_box["left"],
#             new_box["top"],
#             new_box["left"] + new_box["width"],
#             new_box["top"] + new_box["height"],
#         )
#         st.sidebar.write(
#             st.session_state.table_boxes[st.session_state.table_to_edit_idx]
#         )


st.title("PDF Table Edge Detection Adjustment")
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    st.sidebar.title("Adjust Table Edges")

    with pdfplumber.open(uploaded_file) as pdf:
        # for idx, page in enumerate(pdf.pages):

        page = pdf.pages[0]
        im = page.to_image()

        if "page_preview" not in st.session_state:
            # 🍎 PAGE 넘어갈 때마다 RESET
            st.session_state.page_preview = im.original
            st.session_state.table_boxes = []
            st.session_state.next_steps.clear()

        st.image(
            st.session_state.page_preview,
            caption="page preview",
            use_column_width=True,
        )

        if st.session_state.table_boxes == []:
            if st.sidebar.button("모든 테이블 인식"):
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

                st.session_state.next_steps.append("테이블 csv 추출")
                st.rerun()
        else:
            # 테이블 수정
            # if (
            #     st.sidebar.button("테이블 수정 및 제거")
            #     or st.session_state.table_to_edit_idx is not None
            # ):
            table_to_edit = st.sidebar.radio(
                "Select Table to Edit",
                st.session_state.table_boxes,
                key="table_to_edit",
                index=st.session_state.table_to_edit_idx,
                on_change=update_table_to_edit_idx,
                # args=(im,),
            )

            if table_to_edit:
                print("🩷", "editing a table...")
                print(st.session_state.df)
                if (
                    st.sidebar.button(
                        "테이블 범위 수정",
                        disabled=(
                            "테이블 범위 수정" not in st.session_state.next_steps
                        ),
                    )
                    or "canvas"
                    in st.session_state  # need this condition because the widget box is created after running 'adjust_box' more than two times
                ):

                    # canvas로 수정
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
                        st.session_state.table_boxes[
                            st.session_state.table_to_edit_idx
                        ] = (
                            new_box["left"],
                            new_box["top"],
                            new_box["left"] + new_box["width"],
                            new_box["top"] + new_box["height"],
                        )
                        st.sidebar.info(
                            st.session_state.table_boxes[
                                st.session_state.table_to_edit_idx
                            ]
                        )
                    st.session_state.next_steps = ["수정 완료"]

                if st.sidebar.button(
                    "수정 완료",
                    disabled=("수정 완료" not in st.session_state.next_steps),
                ):
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

                if (
                    st.sidebar.button(
                        "테이블 추출",
                        disabled=("테이블 추출" not in st.session_state.next_steps),
                    )
                    or st.session_state.df is not None
                ):
                    box = st.session_state.table_boxes[
                        st.session_state.table_to_edit_idx
                    ]
                    if st.session_state.df is None:
                        new_table = extract_table_content(
                            box,
                            padding=10,
                        )
                        st.session_state.df = pd.DataFrame(
                            new_table
                        )  ## 🍎🍎 TODO: no-index

                    st.dataframe(st.session_state.df, hide_index=True)
                    if st.sidebar.button(
                        "다른 방법으로 재추출",
                        disabled=("테이블 추출" not in st.session_state.next_steps),
                    ):
                        tabula_table = tabula.read_pdf(
                            uploaded_file,
                            area=[box[1], box[0], box[3], box[2]],
                            pages=0,
                            multiple_tables=False,
                            stream=True,
                        )[0]
                        st.session_state.df = tabula_table
                        st.session_state.next_steps = ["테이블 csv 저장"]
                        st.rerun()

                if st.sidebar.button(
                    "테이블 csv 저장",
                    disabled=("테이블 csv 저장" not in st.session_state.next_steps),
                ):
                    export_to_csv()
                    st.session_state.next_steps = [
                        "다음 페이지",
                        "테이블 수정 및 제거",
                    ]

                if st.sidebar.button(
                    "다음 페이지",
                    disabled=("다음 페이지" not in st.session_state.next_steps),
                ):
                    st.session_state.page_idx += 1
                    st.session_state.table_boxes = []
                    st.session_state.table_to_edit_idx = None
                    # st.session_state.df = None

        # else:
        #     # 🍎 page 넘기기 버튼?

        #     st.warning("No edges detected.")
        #     canvas_result = adjust_box(im)
        #     st.session_state.table_boxes = [
        #         (
        #             box["left"],
        #             box["top"],
        #             box["left"] + box["width"],
        #             box["top"] + box["height"],
        #         )
        #         for box in canvas_result.json_data["objects"]  ## 🍎🍎
        #     ]
        #     print("🩷 canvas:", canvas_result.json_data["objects"])

        #     ## Tabula
        #     if st.sidebar.button("Retry Table Detection in Annotated Areas"):
        #         new_boxes = []
        #         for box in st.session_state.table_boxes:

        #             # pdfplumber: (left, top, right, bottom) => tabula: (top, left, bottom, right)
        #             df = tabula.read_pdf(
        #                 uploaded_file,
        #                 area=[box[1], box[0], box[3], box[2]],
        #                 pages=2,
        #                 multiple_tables=False,
        #                 stream=True,
        #             )

        #         # st.session_state.table_boxes = new_boxes
        #         st.session_state.page_preview = draw_boxes(
        #             im.original, st.session_state.table_boxes, color="green"
        #         )  # https://github.com/jsvine/pdfplumber/tree/stable
        #         # st.image(
        #         #     updated_image,
        #         #     caption="Updated Table Edges",
        #         #     use_column_width=True,
        #         # )

        #         st.sidebar.markdown("### Updated Bounding Boxes")
        #         for box in st.session_state.table_boxes:
        #             st.sidebar.write(box)
