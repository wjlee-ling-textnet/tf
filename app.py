import streamlit as st
import pdfplumber
from PIL import Image, ImageDraw

if "page_img" not in st.session_state:
    st.session_state.page_img = None
    st.session_state.table_boxes = None


def draw_boxes(image, boxes, color="red"):
    draw = ImageDraw.Draw(image)
    for box in boxes:
        draw.rectangle(box, outline=color, width=2)
    return image


def update_edges(image, boxes, color):
    st.session_state.page_img = draw_boxes(image, boxes, color=color)
    st.image(
        st.session_state.page_img,
        caption="Detected Edges",
        use_column_width=True,
    )


def main():
    st.title("PDF Table Edge Detection Adjustment")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file is not None:
        st.sidebar.title("Adjust Table Edges")

        with pdfplumber.open(uploaded_file) as pdf:
            page = pdf.pages[0]
            im = page.to_image()
            detected_tables = page.find_tables()

            if detected_tables:
                boxes = [(table.bbox) for table in detected_tables]
                st.session_state.page_img = draw_boxes(im.original, boxes)
                # st.image(
                #     st.session_state.page_img,
                #     caption="Detected Edges",
                #     use_column_width=True,
                # )

                st.sidebar.subheader("Adjust Edges")
                st.session_state.table_boxes = []
                for i, box in enumerate(boxes):
                    st.sidebar.markdown(f"**Edge {i + 1}**")
                    x0 = st.sidebar.slider(
                        f"X0 : Edge {i + 1}",
                        0,
                        int(im.original.width),
                        int(box[0]),
                        on_change=update_edges,
                        args=(im.original, st.session_state.table_boxes, "red"),
                    )
                    y0 = st.sidebar.slider(
                        f"Y0 : Edge {i + 1}",
                        0,
                        int(im.original.height),
                        int(box[1]),
                        on_change=update_edges,
                        args=(im.original, st.session_state.table_boxes, "red"),
                    )
                    x1 = st.sidebar.slider(
                        f"X1 : Edge {i + 1}",
                        0,
                        int(im.original.width),
                        int(box[2]),
                        on_change=update_edges,
                        args=(im.original, st.session_state.table_boxes, "red"),
                    )
                    y1 = st.sidebar.slider(
                        f"Y1 : Edge {i + 1}",
                        0,
                        int(im.original.height),
                        int(box[3]),
                        on_change=update_edges,
                        args=(im.original, st.session_state.table_boxes, "red"),
                    )
                    st.session_state.table_boxes.append((x0, y0, x1, y1))

                if st.sidebar.button("Extract Table"):
                    updated_image = draw_boxes(
                        im.original, st.session_state.table_boxes, color="blue"
                    )
                    st.image(
                        updated_image, caption="Updated Edges", use_column_width=True
                    )

                    st.sidebar.markdown("### Updated Bounding Boxes")
                    for box in st.session_state.table_boxes:
                        st.sidebar.write(box)
            else:
                st.write("No edges detected.")


if __name__ == "__main__":
    main()
