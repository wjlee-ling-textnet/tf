import pickle
import tabula
import pandas as pd
import streamlit as st

from pathlib import Path
from typing import Union
from streamlit import session_state as sst


def extract_table_coordinates_per_page(page, output_dir) -> list:
    # coordinates = []
    detected_tables = page.find_tables()
    if not output_dir.exists():
        output_dir.mkdir(parents=True)

    if detected_tables:
        save_path = output_dir / f"page_{page.page_number}.pkl"
        with save_path.open("wb") as f:
            for table in detected_tables:
                pickle.dump(table.bbox, f)
                # coordinates.append(table.bbox)
    # return coordinates


def load_table_coordinates_per_page(page_idx, output_dir) -> list:
    table_files = list(output_dir.glob(f"page_{page_idx}.pkl"))
    coordinates = []
    for table_file in table_files:
        with table_file.open("rb") as f:
            while True:
                try:
                    bbox = pickle.load(f)
                    coordinates.append(bbox)
                except EOFError:
                    break
    return coordinates


def extract_table_content(page, bbox, padding=7):
    """bbox가 너무 타이트하면 바깥쪽 셀 내용은 추출 못함으로 패딩을 넣어 추출"""
    extended_bbox = (
        bbox[0] - padding if bbox[0] - padding > 0 else 0,
        bbox[1] - padding if bbox[1] - padding > 0 else 0,
        bbox[2] + padding if bbox[2] + padding < page.width else page.width,
        bbox[3] + padding if bbox[3] + padding < page.height else page.height,
    )
    cropped_page = page.within_bbox(extended_bbox)
    new_table = cropped_page.extract_table()
    return new_table


def create_dataframes(page):
    sst.phase = "테이블 내용 수정"

    bbox = (sst.image_bboxes + sst.table_bboxes)[sst.edit_idx]
    padded_table = extract_table_content(page, bbox, padding=10)
    sst.df = pd.DataFrame(padded_table, index=None)  ## TODO: indexing /header 옵션
    sst.tabula_df = tabula.read_pdf(
        sst.uploaded_file,
        area=[bbox[1], bbox[0], bbox[3], bbox[2]],
        pages=sst.user_input_page_idx,
        multiple_tables=False,
        stream=True,
    )[0]
    # st.rerun()


def export_to_markdown(candidate_dfs):
    bbox = (sst.image_bboxes + sst.table_bboxes)[sst.edit_idx]
    bbox_idx = sst.table_bboxes.index(bbox)
    sst.table_bboxes[bbox_idx] = (
        *bbox[:4],
        candidate_dfs[sst.md_candidate_name].to_markdown(),
    )
    # sst.phase = "마크다운 변환"


def extract_tables_per_page_fitz(
    page,
    *,
    output_format: str = "csv",
    output_dir: Union[str, Path] = "tables/",
    strategy: str = "lines",
    vertical_strategy: str = None,
    horizontal_strategy: str = None,
):
    tables = []
    strategies = {}

    if vertical_strategy:
        # 가로줄을 기준으로
        strategies["vertical_strategy"] = vertical_strategy
    if horizontal_strategy:
        # 세로줄을 기준으로
        strategies["horizontal_strategy"] = horizontal_strategy

    ## defaults setting
    if strategies == {}:
        strategies["strategy"] = strategy

    for idx, table in enumerate(page.find_tables(**strategies)):
        if output_format == "dataframe":
            table_df = table.to_pandas()
            table_info = table.bbox + (table_df,)
        elif output_format == "csv":
            if type(output_dir) is str:
                output_dir = Path(output_dir)
            if not output_dir.exists():
                output_dir.mkdir()
            save_path = output_dir / f"{page.number+1}_{idx+1}.csv"
            table_df = table.to_pandas()
            table_df.to_csv(
                save_path,
                index=False,
                escapechar="\\",
            )
            table_info = table.bbox + (save_path,)  # table.bbox + (table_df,)
        elif output_format == "markdown":
            table_info = table.bbox + (table.to_markdown(),)
        else:
            raise ValueError(f"Invalid output format: {output_format}")

        tables.append(table_info)
    return tables
