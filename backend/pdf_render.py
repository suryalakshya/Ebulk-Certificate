from __future__ import annotations

import os
from PIL import Image


def render_pdf_from_png(
    png_path: str,
    output_path: str,
    page_size: tuple[int, int] | None = None,
) -> None:
    """
    Converts a rendered PNG certificate image into a crisp PDF file.
    """
    if not os.path.exists(png_path):
        raise FileNotFoundError(f"PNG file not found: {png_path}")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    with Image.open(png_path) as img:
        img_rgb = img.convert("RGB")
        # Save as PDF using PIL with high DPI quality matching image size
        img_rgb.save(output_path, "PDF", resolution=100.0)
