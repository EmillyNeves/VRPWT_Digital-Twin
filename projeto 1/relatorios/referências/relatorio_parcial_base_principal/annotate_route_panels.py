import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont


PANELS = {
    "route_compare_C_panel_1.png": {"cost": "1113,4", "routes": "11 rotas"},
    "route_compare_C_panel_2.png": {"cost": "903,7", "routes": "11 rotas"},
    "route_compare_C_panel_3.png": {"cost": "833,0", "routes": "10 rotas"},
    "route_compare_C_panel_4.png": {"cost": "827,3", "routes": "10 rotas"},
    "route_compare_C_panel_5.png": {"cost": "865,7", "routes": "11 rotas"},
}

BASE_DIR = Path(__file__).resolve().parent
REFERENCE_PDF = BASE_DIR.parent / "ic_relatorio_parcial_emilly-claudia.pdf"
BOLD_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REGULAR_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
REFERENCE_IMAGES = {
    "route_compare_C_panel_1.png": "panel-000.png",
    "route_compare_C_panel_2.png": "panel-002.png",
    "route_compare_C_panel_3.png": "panel-004.png",
    "route_compare_C_panel_4.png": "panel-006.png",
    "route_compare_C_panel_5.png": "panel-008.png",
}


def restore_reference_panels() -> None:
    pdfimages = shutil.which("pdfimages")
    if pdfimages is None:
        raise RuntimeError("pdfimages nao esta disponivel para restaurar os paineis originais.")
    if not REFERENCE_PDF.exists():
        raise FileNotFoundError(f"PDF de referencia nao encontrado: {REFERENCE_PDF}")

    with tempfile.TemporaryDirectory() as temp_dir:
        output_prefix = Path(temp_dir) / "panel"
        subprocess.run(
            [pdfimages, "-png", str(REFERENCE_PDF), str(output_prefix)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        for panel_name, extracted_name in REFERENCE_IMAGES.items():
            source = Path(temp_dir) / extracted_name
            target = BASE_DIR / panel_name
            if not source.exists():
                raise FileNotFoundError(f"Imagem extraida nao encontrada: {source}")
            shutil.copyfile(source, target)


def add_badge(image_path: Path, cost: str, routes: str) -> None:
    image = Image.open(image_path).convert("RGBA")
    white_bg = Image.new("RGBA", image.size, (255, 255, 255, 255))
    bbox = ImageChops.difference(image, white_bg).getbbox()
    if bbox is not None:
        pad = 6
        left = max(0, bbox[0] - pad)
        top = max(0, bbox[1] - pad)
        right = min(image.size[0], bbox[2] + pad)
        bottom = min(image.size[1], bbox[3] + pad)
        image = image.crop((left, top, right, bottom))

    width, height = image.size
    footer_height = 74
    canvas = Image.new("RGBA", (width, height + footer_height), (255, 255, 255, 255))
    canvas.paste(image, (0, 0))

    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    footer_top = height
    footer_bottom = canvas.size[1]
    top_padding = 10
    bottom_padding = 8
    content_top = footer_top + top_padding
    content_bottom = footer_bottom - bottom_padding
    label_text = "Custo"
    value_text = cost
    routes_text = f"| {routes}"
    max_width = width - 60
    max_height = content_bottom - content_top
    value_font_size = 56
    label_font_size = 50
    routes_font_size = 50
    meta_color = (55, 65, 81, 255)

    while value_font_size > 48:
        label_font = ImageFont.truetype(BOLD_FONT, size=label_font_size)
        value_font = ImageFont.truetype(BOLD_FONT, size=value_font_size)
        routes_font = ImageFont.truetype(BOLD_FONT, size=routes_font_size)

        label_box = draw.textbbox((0, 0), label_text, font=label_font)
        value_box = draw.textbbox((0, 0), value_text, font=value_font)
        routes_box = draw.textbbox((0, 0), routes_text, font=routes_font)

        label_width = label_box[2] - label_box[0]
        value_width = value_box[2] - value_box[0]
        routes_width = routes_box[2] - routes_box[0]

        label_height = label_box[3] - label_box[1]
        value_height = value_box[3] - value_box[1]
        routes_height = routes_box[3] - routes_box[1]

        gap_label = max(10, value_font_size // 6)
        gap_routes = max(16, value_font_size // 4)
        total_width = label_width + gap_label + value_width + gap_routes + routes_width
        total_height = max(label_height, value_height, routes_height)

        if (
            total_width <= max_width
            and total_height <= max_height
        ):
            break

        value_font_size -= 2
        label_font_size = max(46, label_font_size - 2)
        routes_font_size = max(46, routes_font_size - 2)

    label_font = ImageFont.truetype(BOLD_FONT, size=label_font_size)
    value_font = ImageFont.truetype(BOLD_FONT, size=value_font_size)
    routes_font = ImageFont.truetype(BOLD_FONT, size=routes_font_size)

    label_box = draw.textbbox((0, 0), label_text, font=label_font)
    value_box = draw.textbbox((0, 0), value_text, font=value_font)
    routes_box = draw.textbbox((0, 0), routes_text, font=routes_font)

    label_width = label_box[2] - label_box[0]
    value_width = value_box[2] - value_box[0]
    routes_width = routes_box[2] - routes_box[0]

    label_height = label_box[3] - label_box[1]
    value_height = value_box[3] - value_box[1]
    routes_height = routes_box[3] - routes_box[1]

    gap_label = max(10, value_font_size // 6)
    gap_routes = max(16, value_font_size // 4)
    total_width = label_width + gap_label + value_width + gap_routes + routes_width
    total_height = max(label_height, value_height, routes_height)

    y = content_top + max(0, (max_height - total_height) // 2)
    x = (width - total_width) // 2

    draw.text((x, y - label_box[1]), label_text, font=label_font, fill=meta_color)
    x += label_width + gap_label
    draw.text((x, y - value_box[1]), value_text, font=value_font, fill=meta_color)
    x += value_width + gap_routes
    draw.text((x, y - routes_box[1]), routes_text, font=routes_font, fill=meta_color)

    result = Image.alpha_composite(canvas, overlay)
    result.save(image_path)


def main() -> None:
    restore_reference_panels()
    for name, stats in PANELS.items():
        add_badge(BASE_DIR / name, stats["cost"], stats["routes"])


if __name__ == "__main__":
    main()
