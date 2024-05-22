from parsers.image_extract import extract_images_per_page
from parsers.utilities import get_column_boxes

import fitz


def sort_elements_by_bbox(elements: list):
    return sorted(elements, key=lambda ele: (ele[1], ele[0]))


def get_plaintexts(texts: list[tuple], tables: list[tuple]):
    """Since `page.get_text` returns all types of text including table text, we need to filter out the text within a table. The texts and tables contain tuples that are sorted by the coordinates of the bounding box."""
    plaintexts = []
    relevant_tables = []

    table_index = 0
    num_tables = len(tables)

    for text in texts:
        x0, y0, x1, y1, *_ = text  # bounding box of the text box

        relevant_tables = [
            table for table in relevant_tables if table[3] >= y0
        ]  # remove tables from relevant list that are no longer relevant

        while table_index < num_tables and tables[table_index][1] <= y0:
            relevant_tables.append(tables[table_index])
            table_index += 1

        overlap = False
        for table in relevant_tables:
            if x0 >= table[0] and x1 <= table[2] and y0 >= table[1] and y1 <= table[3]:
                overlap = True
                break

        if not overlap:
            plaintexts.append(text)

    return plaintexts


def extract_elements_per_page(pdf_path, save_dir):
    """Extract plain text, images and tables from each page **in order** from a PDF file. Each element has the content (text, image, or table im markdown) as its 5th element, like the .get_text method."""
    doc = fitz.open(pdf_path)
    pages = []
    for page_number in range(len(doc)):
        page = doc[page_number]
        # columns = get_column_boxes(page) # 이미지 추출 후에 해야할지??

        # images
        images, paths = extract_images_per_page(
            doc, page_number, save_dir=save_dir
        )  # list of tuples
        images_bbox = [page.get_image_bbox(img) for img in images]
        images_bbox_with_path = [
            (*img_bbox, path) for img_bbox, path in zip(images_bbox, paths)
        ]

        # tables
        tables = []
        for table in page.find_tables():  # default: find_tables(strategy="lines")
            table_info = table.bbox + (table.to_markdown(),)
            tables.append(table_info)
            # tables_markdown.append(table.to_markdown())

        # plaintexts
        texts = page.get_text(option="blocks")  # list of tuples
        plaintexts = get_plaintexts(texts=texts, tables=tables)

        elements = sort_elements_by_bbox(plaintexts + images_bbox_with_path + tables)
        pages.append(elements)

    return pages


# pages = extract_elements_per_page(
#     "/Users/lwj/workspace/chunky/database/gucheong/금천구청 감사사례집 테스트.pdf",
#     "images/",
# )
# for page in pages:
#     print(page)
#     print("====================================")
