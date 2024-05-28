from pathlib import Path
from typing import Union


def extract_tables_per_page(
    page,
    *,
    output_format: str = "dataframe",
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
                output_dir.mkdir(parents=True)
            save_path = output_dir / f"{page.number}_{idx+1}.csv"
            table_df = table.to_pandas()
            table_df.to_csv(save_path, index=False)
            table_info = table.bbox + (save_path,)  # table.bbox + (table_df,)
        elif output_format == "markdown":
            table_info = table.bbox + (table.to_markdown(),)
        else:
            raise ValueError(f"Invalid output format: {output_format}")

        tables.append(table_info)
    return tables
