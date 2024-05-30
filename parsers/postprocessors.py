import re
import argparse
import pandas as pd
from pathlib import Path


def _replace_link_with_contents(
    element: str, *, save_root_dir: Path, output_format: str = "markdown"
):
    """Meant to be used on manually finalized markdown files, which contain elements seperated by newlines."""
    table_extensions = ("csv", "tsv", "xlsx")
    image_extensions = ("png", "jpg", "jpeg", "bmp", "gif", "tiff")

    pattern = f'[A-Za-z가-힣0-9_\/]+\.({"|".join(table_extensions)})'
    link = re.search(pattern, element)

    # reading a table and converting it to a pandas dataframe
    if link:
        link = link.group()
        path = save_root_dir / link
        if link.endswith("csv"):
            df = pd.read_csv(path)
        elif link.endswith("tsv"):
            df = pd.read_csv(path, sep="\t")
        elif link.endswith("xlsx"):
            df = pd.read_excel(path)

        if output_format == "markdown":
            output = df.to_markdown(index=False)
            return output
        elif output_format == "html":
            output = df.to_html(index=False)
            return output

    return element


def postprocess_pages(
    root_dir: str, output_dir: str = "output", output_format="markdown"
):
    _MAPPING = {"markdown": ".md", "html": ".html"}

    root_dir = Path(root_dir)
    output_dir = root_dir / output_dir
    for p in root_dir.iterdir():
        if not p.is_dir() and p.suffix == _MAPPING[output_format]:
            new_page = []
            with p.open("r", encoding="utf-8") as f:
                page = f.readlines()
                for line in page:
                    line = _replace_link_with_contents(
                        line, save_root_dir=root_dir, output_format=output_format
                    )
                    new_page.append(line)

            new_page = "\n".join(new_page)
            file_save_path = output_dir / p.name
            if not file_save_path.parent.exists():
                file_save_path.parent.mkdir()
            file_save_path.write_text(new_page, encoding="utf-8")

    print("🤖", "Finished binding pages.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "path", type=str, help="Path of the directory of parsed results"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="output",
        help="Output directory for the postprocessed files",
    )
    parser.add_argument(
        "--output_format",
        type=str,
        default="markdown",
        help="Output format for the postprocessed files",
    )

    args = parser.parse_args()
    postprocess_pages(
        args.path, output_dir=args.output_dir, output_format=args.output_format
    )
