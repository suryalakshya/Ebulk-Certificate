from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Literal
from PIL import Image, ImageDraw, ImageFont


@dataclass
class FieldSpec:
    field: str
    x: int
    y: int
    size: int = 40
    align: Literal["left", "center", "right"] = "center"
    font_path: str = "arial.ttf"
    color: str = "#000000"
    bold: bool = False


# Cache loaded fonts for speed
_FONT_CACHE: dict[tuple[str, int, bool], ImageFont.FreeTypeFont | ImageFont.ImageFont] = {}


def get_font(font_name_or_path: str, size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    cache_key = (font_name_or_path, size, bold)
    if cache_key in _FONT_CACHE:
        return _FONT_CACHE[cache_key]

    # Map common font names to Windows system font paths
    windows_fonts_dir = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
    font_map = {
        "arial.ttf": "arial.ttf",
        "arial": "arial.ttf",
        "georgia.ttf": "georgia.ttf",
        "georgia": "georgia.ttf",
        "times.ttf": "times.ttf",
        "times": "times.ttf",
        "courier.ttf": "cour.ttf",
        "courier": "cour.ttf",
        "trebuchet": "trebuc.ttf",
        "verdana": "verdana.ttf",
    }
    
    bold_font_map = {
        "arial.ttf": "arialbd.ttf",
        "arial": "arialbd.ttf",
        "georgia.ttf": "georgiab.ttf",
        "georgia": "georgiab.ttf",
        "times.ttf": "timesbd.ttf",
        "times": "timesbd.ttf",
        "courier.ttf": "courbd.ttf",
        "courier": "courbd.ttf",
    }

    clean_key = os.path.basename(font_name_or_path).lower()
    
    candidate_paths = []
    
    # Custom direct path if exists
    if os.path.exists(font_name_or_path):
        candidate_paths.append(font_name_or_path)

    # Check bold variant if requested
    if bold:
        if clean_key in bold_font_map:
            candidate_paths.append(os.path.join(windows_fonts_dir, bold_font_map[clean_key]))

    # Check standard variant
    if clean_key in font_map:
        candidate_paths.append(os.path.join(windows_fonts_dir, font_map[clean_key]))

    # Generic check in Windows fonts directory
    candidate_paths.append(os.path.join(windows_fonts_dir, font_name_or_path))

    # Try loading truetype font
    font = None
    for path in candidate_paths:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, size=size)
                break
            except Exception:
                pass

    if font is None:
        try:
            # Try default truetype or standard fallback
            font = ImageFont.truetype("arial.ttf", size=size)
        except Exception:
            font = ImageFont.load_default()

    _FONT_CACHE[cache_key] = font
    return font


def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    hex_str = hex_str.lstrip("#")
    if len(hex_str) == 3:
        hex_str = "".join(c * 2 for c in hex_str)
    if len(hex_str) == 6:
        try:
            return (
                int(hex_str[0:2], 16),
                int(hex_str[2:4], 16),
                int(hex_str[4:6], 16),
            )
        except ValueError:
            pass
    return (0, 0, 0)


def render_certificate_png(
    template_path: str,
    output_path: str,
    row: dict[str, Any],
    fields: list[FieldSpec],
    y_mode: str = "top",
) -> tuple[int, int]:
    """
    Renders dynamic text onto the certificate template image using Pillow.
    Returns (width, height) page dimensions.
    """
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template image not found at: {template_path}")

    # Open base image and convert to RGBA / RGB
    with Image.open(template_path) as img:
        img = img.convert("RGB")
        width, height = img.size
        draw = ImageDraw.Draw(img)

        for field in fields:
            value = str(row.get(field.field, "") or "").strip()
            if not value:
                continue

            font = get_font(field.font_path, field.size, bold=field.bold)
            color_rgb = hex_to_rgb(field.color)

            # Measure text size using getbbox
            bbox = draw.textbbox((0, 0), value, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # Calculate X based on alignment
            draw_x = field.x
            if field.align == "center":
                draw_x = field.x - (text_width / 2.0)
            elif field.align == "right":
                draw_x = field.x - text_width

            draw_y = field.y
            if y_mode == "center":
                draw_y = field.y - (text_height / 2.0)

            # Draw text
            draw.text((draw_x, draw_y), value, fill=color_rgb, font=font)

        # Ensure target directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        img.save(output_path, "PNG", quality=95)

    return width, height
