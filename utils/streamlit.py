import streamlit as st

from typing import Union, List
from pathlib import Path
from PIL import Image, ImageDraw
from streamlit import session_state as sst
from streamlit_drawable_canvas import st_canvas


def make_button(label):
    return st.sidebar.button(label, disabled=(label not in sst.next_steps))


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


def add_table(canvas_result):
    # with column:
    #     canvas_result = show_canvas(image, key="add_canvas")
    if canvas_result.json_data is not None and len(canvas_result.json_data["objects"]):
        new_box = canvas_result.json_data["objects"][0]
        new_box = (
            new_box["left"],
            new_box["top"],
            new_box["left"] + new_box["width"],
            new_box["top"] + new_box["height"],
        )
        if new_box not in sst.table_bboxes:
            sst.table_bboxes.append(new_box)
        # st.sidebar.info(sst.table_bboxes[-1])
        return new_box
    return None


def adjust_bbox(canvas_result, page_img):

    if canvas_result.json_data is not None and len(canvas_result.json_data["objects"]):
        new_box = canvas_result.json_data["objects"][0]
        new_box = (
            new_box["left"],
            new_box["top"],
            new_box["left"] + new_box["width"],
            new_box["top"] + new_box["height"],
        )
        old_bbox_name = (sst.image_bboxes + sst.table_bboxes)[sst.edit_idx]
        if old_bbox_name in sst.table_bboxes:
            idx = sst.table_bboxes.index(old_bbox_name)
            sst.table_bboxes[idx] = new_box
        else:
            idx = sst.image_bboxes.index(old_bbox_name)
            sst.image_bboxes[idx] = new_box

        sst.page_preview = draw_boxes(
            page_img.original,
            sst.image_bboxes + sst.table_bboxes,
            colors=["green"] * len(sst.image_bboxes) + ["blue"] * len(sst.table_bboxes),
        )

        return new_box
    return None


def show_canvas(_page_image, box=None, **kwargs):
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


def update_edit_idx(img):
    # if (
    #     "element_to_edit" in sst
    #     and sst.element_to_edit is not None
    # ):
    sst.phase = "요소 selectbox"
    sst.edit_idx = (sst.image_bboxes + sst.table_bboxes).index(sst.element_to_edit)

    colors = ["green"] * len(sst.image_bboxes) + ["blue"] * len(sst.table_bboxes)
    colors[sst.edit_idx] = "red"
    sst.page_preview = draw_boxes(
        img,
        sst.image_bboxes + sst.table_bboxes,
        colors=colors,
    )


def check_process(boxes: list[tuple]):
    """
    Before constructing the final markdown of a page, check if each bounding box consists of more than 4 elements (coordinates), meaning that it has been parsed and processed.
    """
    if boxes:
        for box in boxes:
            if len(box) <= 4:
                st.warning("검수 및 마크다운 전환이 되지 않은 요소가 있습니다.")
                return False
    return True


def sort_elements_by_bbox(elements: list):
    return sorted(elements, key=lambda ele: (ele[1], ele[0]))


def _create_hyperlink(element, save_root_dir: Path):
    table_extensions = (".csv", ".tsv", ".xlsx")
    image_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff")
    if element.endswith(table_extensions) or element.endswith(image_extensions):
        element = element.lstrip(save_root_dir.__str__()).lstrip("/")
        # element = (
        #     "/".join(element.split("/")[1:])
        #     if element.startswith("sample/")
        #     else element
        # )
        return f"[{element}]({element})"
    else:
        return element


def reconstruct_page_from_elements(elements: list, save_root_dir: Path):
    "Given elements, sorted by their bounding box, reconstruct a page in markdown format by removing the bounding box information."
    page_content = ""
    for element in elements:
        if type(element[4]) == str:
            page_content += element[4]
        else:
            page_content += _create_hyperlink(
                str(element[4]), save_root_dir=save_root_dir
            )

        if not page_content.endswith("\n"):
            page_content += "\n"

    return page_content
