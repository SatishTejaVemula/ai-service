from pathlib import Path
from pptx import Presentation


def extract_ppt_text(file_path: str) -> str:
    """
    Extract all readable text from a PowerPoint presentation.

    Args:
        file_path: Absolute or relative path to the PPT/PPTX file.

    Returns:
        A single string containing the text from every slide.
    """

    ppt_path = Path(file_path).resolve()

    print(f"Opening PPT: {ppt_path}")

    if not ppt_path.exists():
        raise FileNotFoundError(f"PPT file not found: {ppt_path}")

    presentation = Presentation(str(ppt_path))

    extracted_text = []

    for slide_index, slide in enumerate(presentation.slides, start=1):

        extracted_text.append(
            f"\n==================== Slide {slide_index} ====================\n"
        )

        for shape in slide.shapes:

            if getattr(shape, "has_text_frame", False):

                text = shape.text.strip()

                if text:
                    extracted_text.append(text)

    final_text = "\n".join(extracted_text).strip()

    if not final_text:
        final_text = "No readable text found in the PowerPoint."

    return final_text