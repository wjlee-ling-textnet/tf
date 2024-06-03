import streamlit as st
import pdfplumber
from PIL import Image, ImageDraw
from streamlit import experimental_rerun
from streamlit_drawable_canvas import st_canvas


if "table_boxes" not in st.session_state:
    st.session_state.table_boxes = None
    st.session_state.editor_mode = False


def draw_boxes(image, boxes, color="red"):
    draw = ImageDraw.Draw(image)
    for box in boxes:
        draw.rectangle(box, outline=color, width=2)
    return image


def adjust_box(page_image, box=None):
    im_pil = page_image.original.convert("RGB")
    canvas_image = Image.new("RGB", im_pil.size, (255, 255, 255))
    canvas_image.paste(im_pil)

    kwargs = {
        "fill_color": "rgba(255, 165, 0, 0.3)",
        "stroke_width": 2,
        "stroke_color": "blue",
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


st.title("PDF Table Edge Detection Adjustment")
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    st.sidebar.title("Adjust Table Edges")

    with pdfplumber.open(uploaded_file) as pdf:
        # for idx, page in enumerate(pdf.pages):

        page = pdf.pages[1]
        im = page.to_image()

        if "page_preview" not in st.session_state:
            # 🍎 PAGE 넘어갈 때마다 RESET
            st.session_state.page_preview = im.original

        st.image(
            st.session_state.page_preview,
            caption="Original",
            use_column_width=True,
        )

        detected_tables = page.find_tables()
        if detected_tables:
            boxes = [(table.bbox) for table in detected_tables]
            st.session_state.page_preview = draw_boxes(im.original, boxes)

            canvas_result = adjust_box(im, boxes[0])
            st.session_state.table_boxes = [
                (box["x1"], box["y1"], box["x2"], box["y2"])
                for box in canvas_result.json_data["objects"]
            ]

            print(canvas_result.json_data["objects"])
            # print(canvas_result.json_data["shapes"])
            """
            [{'type': 'rect', 'version': '4.4.0', 'originX': 'left', 'originY': 'top', 'left': 68, 'top': 356, 'width': 192, 'height': 79, 'fill': 'rgba(255, 165, 0, 0.3)', 'stroke': 'blue', 'strokeWidth': 2, 'strokeDashArray': None, 'strokeLineCap': 'butt', 'strokeDashOffset': 0, 'strokeLineJoin': 'miter', 'strokeUniform': True, 'strokeMiterLimit': 4, 'scaleX': 1, 'scaleY': 1, 'angle': 0, 'flipX': False, 'flipY': False, 'opacity': 1, 'shadow': None, 'visible': True, 'backgroundColor': '', 'fillRule': 'nonzero', 'paintFirst': 'fill', 'globalCompositeOperation': 'source-over', 'skewX': 0, 'skewY': 0, 'rx': 0, 'ry': 0}]
            """
            # if canvas_result.json_data:
            #     st.session_state.table_boxes = [
            #         (shape["x1"], shape["y1"], shape["x2"], shape["y2"])
            #         for shape in canvas_result.json_data["shapes"]
            #     ]

            if st.sidebar.button("Retry Table Detection in Annotated Areas"):
                new_boxes = []
                for box in st.session_state.table_boxes:
                    cropped_page = page.within_bbox(box)
                    new_tables = cropped_page.find_tables()
                    for table in new_tables:
                        new_boxes.append(table.bbox)

                st.session_state.table_boxes = new_boxes
                updated_image = draw_boxes(im.original, new_boxes, color="blue")
                st.image(
                    updated_image,
                    caption="Updated Table Edges",
                    use_column_width=True,
                )

                st.sidebar.markdown("### Updated Bounding Boxes")
                for box in st.session_state.table_boxes:
                    st.sidebar.write(box)

            # if st.sidebar.button("Extract Table"):
            #     updated_image = draw_boxes(
            #         im.original, st.session_state.table_boxes, color="blue"
            #     )
            #     st.image(
            #         updated_image,
            #         caption="Updated Edges",
            #         use_column_width=True,
            #     )

            #     st.sidebar.markdown("### Updated Bounding Boxes")
            #     for box in st.session_state.table_boxes:
            #         st.sidebar.write(box)
        else:
            st.warning("No edges detected.")
            canvas_result = adjust_box(im)
            st.session_state.table_boxes = [
                (
                    box["left"],
                    box["top"],
                    box["left"] + box["width"],
                    box["top"] + box["height"],
                )  # 'left': 67, 'top': 135, 'width': 466, 'height': 622,
                for box in canvas_result.json_data["objects"]
            ]

            if st.sidebar.button("Retry Table Detection in Annotated Areas"):
                new_boxes = []
                for box in st.session_state.table_boxes:
                    cropped_page = page.within_bbox(box)
                    new_tables = cropped_page.extract_table()
                    for table in new_tables:
                        new_boxes.append(table.bbox)
                print("🩷", new_boxes)
                st.session_state.table_boxes = new_boxes
                updated_image = draw_boxes(im.original, new_boxes, color="green")
                st.image(
                    updated_image,
                    caption="Updated Table Edges",
                    use_column_width=True,
                )

                st.sidebar.markdown("### Updated Bounding Boxes")
                for box in st.session_state.table_boxes:
                    st.sidebar.write(box)
