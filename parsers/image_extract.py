import fitz


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


def extract_and_save_images_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)  # Open the PDF file

    for page_number in range(len(doc)):
        page = doc[page_number]
        # Extract images
        image_list = page.get_images(full=True)

        # Save images found on the current page
        for img_index, img in enumerate(image_list, 1):
            xref = img[0]  # xref is the reference number for the image
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]  # The image in bytes
            image_ext = base_image["ext"]  # The image file extension

            # Write the image to a file
            image_filename = f"image_{page_number+1}_{img_index}.{image_ext}"
            with open(image_filename, "wb") as img_file:
                img_file.write(image_bytes)
            print(f"Saved image to {image_filename}")

    doc.close()


images = extract_and_save_images_from_pdf(
    "/Users/lwj/workspace/chunky/database/yonsei/연도별졸업요건_2024.pdf"
)
# print(images[0])  # -> (19, 0, 226, 200, 8, 'DeviceRGB', '', 'Im1', 'DCTDecode', 0)
# print(images[1])  #  -> (791, 0, 1913, 337, 8, 'DeviceRGB', '', 'Im2', 'DCTDecode', 0)
