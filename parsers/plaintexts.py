def _join_text_boxes(prev_boxes: list[tuple], curr_box: tuple) -> list[tuple]:
    """Join the current text box to the previous text boxe if they have the same y-coordinates('top's) and sizes.
    The inputs should be of the format (x0, y0 or top, x1, y1 or bottom, text, size)
    """
    if len(prev_boxes) == 0:
        return [curr_box]
    else:
        prev_box = prev_boxes[-1]
        if prev_box[1] == curr_box[1] and prev_box[5] == curr_box[5]:
            if prev_box[3] != curr_box[3]:
                print(prev_box[3], curr_box[3])
                raise ValueError("y0은 같은데 y1이 다름")

            new_x1 = curr_box[2]  # elongate x1
            new_text = " ".join([prev_box[4], curr_box[4]])  # join text

            joined_box = (
                prev_box[0],
                prev_box[1],
                new_x1,
                prev_box[3],
                new_text,
                prev_box[5],
            )
            prev_boxes[-1] = joined_box
        else:
            prev_boxes.append(curr_box)
        return prev_boxes


def get_plaintext_boxes(texts: list[dict], tables: list[tuple]):
    """
    Remove duplicate text boxes that are overlapped with table boxes.
    """
    plaintexts = []
    for text_dict in texts:
        text, x0, top, x1, bottom, size, fontname = (
            text_dict["text"],
            text_dict["x0"],
            text_dict["top"],
            text_dict["x1"],
            text_dict["bottom"],
            text_dict["size"],
            text_dict["fontname"],
        )  # additionally available: 'doctop', 'upright', 'height', 'width', 'direction'

        # check if overlaps with any table
        overlap = False
        for table in tables:
            if (
                x0 >= table[0]
                and x1 <= table[2]
                and top >= table[1]
                and bottom <= table[3]
            ):
                # if the text box is inside the table box
                overlap = True
                break

        if not overlap:
            plaintexts = _join_text_boxes(
                plaintexts, (x0, top, x1, bottom, text, size, fontname)
            )

    return plaintexts
