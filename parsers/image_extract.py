import fitz

from pathlib import Path


def extract_images(pdf_path):
    """Extract the metadata of images from a PDF file."""
    # Open the PDF file
    pdf_file = fitz.open(pdf_path)

    images = []
    # Iterate over each page
    for page_num in range(pdf_file.page_count):
        # Get the page
        page = pdf_file[page_num]

        images.extend(page.get_images(full=True))

    pdf_file.close()
    return images


def extract_images_per_page(doc, page_number, save_dir: str = "images/"):
    page = doc[page_number]
    save_dir_path = Path(save_dir)
    if not save_dir_path.exists():
        save_dir_path.mkdir()

    # Extract images
    images = page.get_images(full=True)

    paths = []
    # Save images found on the current page
    for img_index, img in enumerate(images, 1):
        xref = img[0]  # xref is the reference number for the image
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]  # The image in bytes
        image_ext = base_image["ext"]  # The image file extension

        # Write the image to a file
        image_save_path = (
            save_dir_path / f"image_{page_number+1}_{img_index}.{image_ext}"
        )
        with image_save_path.open("wb") as img_file:
            img_file.write(image_bytes)

        # Add the image save path to the 'image' tuple
        # Cannot append it to the end of the original tuple because it checks whether the the last item of the tuple is a int or not
        # images[img_index - 1] = (*img[:4], image_save_path, *img[5:])
        paths.append(image_save_path)

    print(f"Saved {len(images)} image(s) to {save_dir_path._str}")
    return images, paths


def extract_and_save_images_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)  # Open the PDF file

    output = []
    for page_number in range(len(doc)):
        output.extend(extract_images_per_page(doc, page_number))

    doc.close()
    return output


# doc = fitz.open(
#     "/Users/lwj/workspace/chunky/database/gucheong/금천구청 감사사례집 테스트.pdf"
# )
# images = extract_and_save_images_from_pdf(
#     "/Users/lwj/workspace/chunky/database/gucheong/금천구청 감사사례집 테스트.pdf"
# )
# img = doc[3].get_image_bbox(images[-2])
# cnt = doc[3].get_text(option="blocks")
# print(img)
# print("====================================")
# print(cnt)
