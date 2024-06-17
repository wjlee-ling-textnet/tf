# from parsers.image_extract import extract_images_per_page
# from parsers.tables import extract_tables_per_page
# from parsers.utilities import get_column_boxes

# import argparse
# import fitz

# # import tika
# import pdfplumber
# from typing import Union
# from pathlib import Path

# # from tika import parser as tika_parser
# from tqdm import tqdm

# # from unstructured.partition.pdf import partition_pdf


# def sort_elements_by_bbox(elements: list):
#     return sorted(elements, key=lambda ele: (ele[1], ele[0]))


# def _create_hyperlink(element, save_root_dir: Path):
#     table_extensions = (".csv", ".tsv", ".xlsx")
#     image_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff")
#     if element.endswith(table_extensions) or element.endswith(image_extensions):
#         element = element.lstrip(save_root_dir.__str__()).lstrip("/")
#         # element = (
#         #     "/".join(element.split("/")[1:])
#         #     if element.startswith("sample/")
#         #     else element
#         # )
#         return f"[{element}]({element})"
#     else:
#         return element


# def reconstruct_page_from_elements(elements: list, save_root_dir: Path):
#     "Given elements, sorted by their bounding box, reconstruct a page in markdown format by removing the bounding box information."
#     page_content = ""
#     for element in elements:
#         if type(element[4]) == str:
#             page_content += element[4]
#         else:
#             page_content += _create_hyperlink(
#                 str(element[4]), save_root_dir=save_root_dir
#             )

#         if not page_content.endswith("\n"):
#             page_content += "\n"

#     return page_content


# def get_plaintexts(texts: list[tuple], tables: list[tuple]):
#     """Since `page.get_text` returns all types of text including table text, we need to filter out the text within a table. The texts and tables contain tuples that are sorted by the coordinates of the bounding box."""
#     plaintexts = []
#     relevant_tables = []

#     table_index = 0
#     num_tables = len(tables)

#     for text in texts:
#         x0, y0, x1, y1, *_ = text  # bounding box of the text box

#         relevant_tables = [
#             table for table in relevant_tables if table[3] >= y0
#         ]  # remove tables from relevant list that are no longer relevant

#         while table_index < num_tables and tables[table_index][1] <= y0:
#             relevant_tables.append(tables[table_index])
#             table_index += 1

#         overlap = False
#         for table in relevant_tables:
#             if x0 >= table[0] and x1 <= table[2] and y0 >= table[1] and y1 <= table[3]:
#                 overlap = True
#                 break

#         if not overlap:
#             plaintexts.append(text)

#     return plaintexts


# def extract_elements_fitz(
#     pdf_path,
#     *,
#     save_root_dir: Path,
#     page_range: Union[str, int] = "all",
#     image_config: dict = {},
#     table_config: dict = {},
# ) -> Union[list[tuple], list[list[tuple]]]:
#     """Extract plain text, images and tables from each page **in order** from a PDF file. Each element has the content (text, image, or table im markdown) as its 5th element, like the .get_text method."""
#     doc = fitz.open(pdf_path)
#     pages = []
#     table_save_dir = save_root_dir / table_config.get("output_dir", "tables/")
#     image_save_dir = save_root_dir / image_config.get("output_dir", "images/")

#     if page_range == "all":
#         for page_number in range(len(doc)):
#             page = doc[page_number]
#             # columns = get_column_boxes(page) # 이미지 추출 후에 해야할지??

#             # images

#             images, paths = extract_images_per_page(
#                 doc, page_number, output_dir=image_save_dir
#             )  # list of tuples
#             images_bbox = [page.get_image_bbox(img) for img in images]
#             images_bbox_with_path = [
#                 (*img_bbox, path) for img_bbox, path in zip(images_bbox, paths)
#             ]

#             # tables
#             tables = extract_tables_per_page(
#                 page, **table_config, output_dir=table_save_dir
#             )

#             # plaintexts
#             texts = page.get_text(option="blocks")  # list of tuples
#             plaintexts = get_plaintexts(texts=texts, tables=tables)

#             elements = sort_elements_by_bbox(
#                 plaintexts + images_bbox_with_path + tables
#             )
#             pages.append(elements)
#         return pages
#     else:
#         page_number = int(page_range)
#         page = doc[page_number]

#         # images
#         images, paths = extract_images_per_page(
#             doc, page_number, output_dir=image_save_dir
#         )  # list of tuples
#         images_bbox = [page.get_image_bbox(img) for img in images]
#         images_bbox_with_path = [
#             (*img_bbox, path) for img_bbox, path in zip(images_bbox, paths)
#         ]

#         # tables
#         tables = extract_tables_per_page(
#             page, **table_config, output_dir=table_save_dir
#         )

#         # plaintexts
#         texts = page.get_text(option="blocks")  # list of tuples
#         plaintexts = get_plaintexts(texts=texts, tables=tables)

#         elements = sort_elements_by_bbox(plaintexts + images_bbox_with_path + tables)
#         return elements


# def parse_pdf_fitz(
#     pdf_path, *, page_range=None, save_root_dir=None, image_config={}, table_config={}
# ):
#     doc = fitz.open(pdf_path)
#     file_name = pdf_path.split("/")[-1].split(".")[0].replace(" ", "_")
#     if save_root_dir is None:
#         save_root_dir = Path(file_name)
#     else:
#         save_root_dir = Path(save_root_dir)
#     if not save_root_dir.exists():
#         save_root_dir.mkdir(parents=True)

#     if page_range is None or page_range == "all":
#         start_idx, end_idx = 0, len(doc)
#     else:
#         if "-" in page_range:
#             start_idx, end_idx = map(int, page_range.split("-"))
#             start_idx -= 1
#         else:
#             start_idx, end_idx = int(page_range) - 1, int(page_range)

#     assert start_idx <= end_idx, "Invalid page range"
#     assert end_idx <= len(doc), "Invalid page range"
#     if start_idx < 0:
#         start_idx = 0
#     assert start_idx >= 0, "Invalid page range"

#     for page_number in tqdm(range(start_idx, end_idx)):
#         elements = extract_elements_fitz(
#             pdf_path,
#             page_range=page_number,
#             image_config=image_config,
#             table_config=table_config,
#             save_root_dir=save_root_dir,
#         )
#         page_content = reconstruct_page_from_elements(
#             elements, save_root_dir=save_root_dir
#         )
#         with open(save_root_dir / f"page_{page_number+1}.md", "w") as f:
#             f.write(page_content)


# # def extract_tables_unstructured(pdf_path):
# #     elements = partition_pdf(
# #         filename=pdf_path,
# #         infer_table_structure=True,
# #         langauges=["kor", "eng"],
# #         extract_images_in_pdf=True,
# #         # strategy="hi_res",
# #     )
# #     tables = []
# #     for el in elements:
# #         if el.category == "Table":
# #             tables.append(el.metadata.text_as_html)
# #             # tables.append(el.text)
# #     return tables


# def extract_text_tika(pdf_path):
#     """Only text can be extracted without its structure/format (e.g. table) from the PDF file using Tika."""
#     tika.initVM()
#     parsed = tika_parser.from_file(pdf_path, xmlContent=True)

#     # print(parsed["content"])
#     # print(parsed["metadata"])
#     return parsed


# def extract_elements_per_page_pdfplumber(pdf_path):
#     with pdfplumber.open(pdf_path) as pdf:
#         for num, page in enumerate(pdf.pages, 1):
#             print(f"Page {num}")
#             table_settings = {
#                 "vertical_strategy": "text",
#                 "horizontal_strategy": "lines",
#             }
#             tables = page.extract_tables(table_settings)
#             for table in tables:
#                 for row in table:
#                     print(row)


# if __name__ == "__main__":
#     parser = argparse.ArgumentParser()
#     parser.add_argument("path", type=str, help="Path to the PDF file")
#     parser.add_argument(
#         "-fn", "--function", type=str, default="parse_pdf_fitz", help="Function name"
#     )
#     parser.add_argument("--save_dir", type=str, help="Path to the root save directory")
#     parser.add_argument("--page_range", type=str, default="all", help="Page number")
#     parser.add_argument(
#         "-ic", "--image_config", type=str, default="{}", help="Image config"
#     )
#     parser.add_argument(
#         "-tc", "--table_config", type=str, default="{}", help="Table config"
#     )

#     args = parser.parse_args()
#     table_config = eval(args.table_config)
#     image_config = eval(args.image_config)

#     if args.function == "extract_elements_fitz":
#         pages = extract_elements_fitz(
#             args.path, args.page_range, image_config, table_config
#         )
#         print(pages)

#     elif args.function == "parse_pdf_fitz":
#         pages = parse_pdf_fitz(
#             args.path,
#             page_range=args.page_range,
#             image_config=image_config,
#             table_config=table_config,
#         )

#     # elif args.function == "extract_tables_unstructured":
#     #     tables = extract_tables_unstructured(args.path)
#     #     print(tables)

#     # elif args.function == "extract_text_tika":
#     #     parsed = extract_text_tika(args.path)
#     #     print(parsed)

#     # elif args.function == "extract_elements_per_page_pdfplumber":
#     #     extract_elements_per_page_pdfplumber(args.path)

#     else:
#         print("Invalid function name")
