def extract_tables_per_page(
    page,
    output_format: str = "dataframe",
    *,
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

    for table in page.find_tables(**strategies):
        if output_format == "dataframe":
            table_info = table.bbox + (table.to_pandas(),)
        elif output_format == "markdown":
            table_info = table.bbox + (table.to_markdown(),)
        tables.append(table_info)
    return tables
