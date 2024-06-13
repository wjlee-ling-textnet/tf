from collections import namedtuple
from pathlib import Path
from pdfminer.image import ImageWriter


def extract_images_per_page(page, output_dir: str = "images/") -> None:
    """
    Convert the images metadata to fit the format of pdfminer.six's ImageWriter
    ref: https://github.com/pdfminer/pdfminer.six/blob/d79bcb75ea08442df0c69af050c0070d0ae036b4/pdfminer/image.py#L72
    Saved images under '{sst.root_dir}/images/page{sst.page_idx+1}_(x0,top,x1,bottom).{ext}'
    """

    keys = [
        "x0",
        "y0",
        "x1",
        "y1",
        "width",
        "height",
        "stream",
        "srcsize",
        "imagemask",
        "bits",
        "colorspace",
        "mcid",
        "tag",
        "object_type",
        "page_number",
        "top",
        "bottom",
        "doctop",
        "name",  ## added for pdfminer.six
    ]
    writer = ImageWriter(output_dir)
    for img in page.images:
        element = (
            img["x0"],
            img["top"],
            img["x1"],
            img["top"] + img["height"],
        )
        img["name"] = f"page{img['page_number']}_{element}"
        new_info = {key: img[key] for key in keys}
        dict_as_tuple = namedtuple("dict_as_tuple", new_info)
        img_tuple = dict_as_tuple(**new_info)
        writer.export_image(img_tuple)