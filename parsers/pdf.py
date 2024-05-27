from parsers.image_extract import extract_images_per_page
from parsers.utilities import get_column_boxes

import fitz
import tika
import pdfplumber
from tika import parser as tika_parser
from unstructured.partition.pdf import partition_pdf
import argparse


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


def extract_elements_per_page(pdf_path, save_dir, table_config: dict = {}):
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
        for table in page.find_tables(
            **table_config
        ):  # default: find_tables(strategy="lines")
            table_info = table.bbox + (table.to_markdown(),)
            tables.append(table_info)
            # tables_markdown.append(table.to_markdown())

        # plaintexts
        texts = page.get_text(option="blocks")  # list of tuples
        plaintexts = get_plaintexts(texts=texts, tables=tables)

        elements = sort_elements_by_bbox(plaintexts + images_bbox_with_path + tables)
        pages.append(elements)

    return pages


def extract_tables_unstructured(pdf_path):
    elements = partition_pdf(
        filename=pdf_path,
        infer_table_structure=True,
        langauges=["kor", "eng"],
        extract_images_in_pdf=True,
        # strategy="hi_res",
    )
    tables = []
    for el in elements:
        if el.category == "Table":
            tables.append(el.metadata.text_as_html)
            # tables.append(el.text)
    return tables


def extract_text_tika(pdf_path):
    """Only text can be extracted without its structure/format (e.g. table) from the PDF file using Tika."""
    tika.initVM()
    parsed = tika_parser.from_file(pdf_path, xmlContent=True)

    # print(parsed["content"])
    # print(parsed["metadata"])
    return parsed


def extract_elements_per_page_pdfplumber(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        for num, page in enumerate(pdf.pages, 1):
            print(f"Page {num}")
            table_settings = {
                "vertical_strategy": "text",
                "horizontal_strategy": "lines",
            }
            tables = page.extract_tables(table_settings)
            for table in tables:
                for row in table:
                    print(row)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("fn", type=str, help="Function name")
    parser.add_argument("pdf_path", type=str, help="Path to the PDF file")
    parser.add_argument("page", type=str, default="all", help="Page number")
    parser.add_argument("-tc", "--table_config", type=dict, help="Table config")

    args = parser.parse_args()

    if args.fn == "extract_elements_per_page":
        pages = extract_elements_per_page(args.pdf_path)
        print(pages)
    elif args.fn == "extract_tables_unstructured":
        tables = extract_tables_unstructured(args.pdf_path)
        print(tables)
    elif args.fn == "extract_text_tika":
        parsed = extract_text_tika(args.pdf_path)
        print(parsed)
    elif args.fn == "extract_elements_per_page_pdfplumber":
        extract_elements_per_page_pdfplumber(args.pdf_path)
    else:
        print("Invalid function name")
