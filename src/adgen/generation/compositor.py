from functools import cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageStat

from adgen.core.config import FONTS

Box = tuple[int, int, int, int]

FONT_FAMILIES = {
    "serif": FONTS / "PlayfairDisplay.ttf",
    "condensed": FONTS / "Oswald.ttf",
    "sans": FONTS / "Inter.ttf",
}
HEADLINE_WEIGHT = 700
TEXT_REGIONS = {
    "top_left": (0.06, 0.06, 0.60, 0.34),
    "top_right": (0.40, 0.06, 0.94, 0.34),
    "top_band": (0.08, 0.05, 0.92, 0.27),
    "bottom_left": (0.06, 0.66, 0.60, 0.94),
}
LINE_SPACING = 1.12
DARK_BACKGROUND_LUMINANCE = 140


def font_family(typography_hint: str) -> str:
    hint = typography_hint.lower()
    if "condensed" in hint:
        return "condensed"
    if "serif" in hint and "sans" not in hint:
        return "serif"
    return "sans"


@cache
def load_font(family: str, size: int) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(FONT_FAMILIES[family]), size)
    axes = font.get_variation_axes()
    font.set_variation_by_axes([HEADLINE_WEIGHT if axis["name"] == b"Weight" else axis["default"] for axis in axes])
    return font


def region_box(image: Image.Image, region: str) -> Box:
    w, h = image.size
    left, top, right, bottom = TEXT_REGIONS[region]
    return int(left * w), int(top * h), int(right * w), int(bottom * h)


def overlaps(a: Box, b: Box) -> bool:
    return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])


def quietest_region(image: Image.Image, avoid: Box | None = None) -> str:
    edges = image.convert("L").filter(ImageFilter.FIND_EDGES)

    def busyness(region: str) -> float:
        box = region_box(image, region)
        if avoid and overlaps(box, avoid):
            return float("inf")
        return ImageStat.Stat(edges.crop(box)).mean[0]

    return min(TEXT_REGIONS, key=busyness)


def wrap_lines(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    return [*lines, current]


def contrast_colour(image: Image.Image, box: Box) -> tuple[int, int, int]:
    background = ImageStat.Stat(image.crop(box)).mean[:3]
    luminance = 0.299 * background[0] + 0.587 * background[1] + 0.114 * background[2]
    if luminance < DARK_BACKGROUND_LUMINANCE:
        return tuple(min(255, int(235 + c * 0.08)) for c in background)
    return tuple(int(c * 0.18) for c in background)


def overlay_headline(image: Image.Image, text: str, typography_hint: str = "", avoid: Box | None = None) -> Image.Image:
    canvas = image.convert("RGB").copy()
    region = quietest_region(canvas, avoid)
    left, top, right, bottom = region_box(canvas, region)
    draw = ImageDraw.Draw(canvas)
    family = font_family(typography_hint)

    size = int((bottom - top) * 0.45)
    while True:
        font = load_font(family, size)
        lines = wrap_lines(draw, text, font, right - left)
        line_height = int(size * LINE_SPACING)
        fits = len(lines) * line_height <= bottom - top and all(draw.textlength(line, font=font) <= right - left for line in lines)
        if fits or size <= 14:
            break
        size -= 2

    colour = contrast_colour(canvas, (left, top, right, bottom))
    for index, line in enumerate(lines):
        width = draw.textlength(line, font=font)
        x = left if "left" in region else right - width if "right" in region else (left + right - width) / 2
        draw.text((x, top + index * line_height), line, font=font, fill=colour)
    return canvas


def product_cutout(reference_path: Path) -> Image.Image:
    from rembg import remove

    cutout = remove(Image.open(reference_path).convert("RGB"))
    return cutout.crop(cutout.getbbox())


def composite_product(background: Image.Image, cutout: Image.Image, height_ratio: float = 0.48) -> tuple[Image.Image, Box]:
    canvas = background.convert("RGBA").copy()
    w, h = canvas.size
    scale = min(h * height_ratio / cutout.height, w * 0.5 / cutout.width)
    product = cutout.resize((int(cutout.width * scale), int(cutout.height * scale)), Image.LANCZOS)
    x = int(w * 0.62 - product.width / 2)
    y = int(h * 0.92 - product.height)

    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse(
        (x + product.width * 0.08, y + product.height * 0.94, x + product.width * 0.92, y + product.height * 1.04),
        fill=(0, 0, 0, 110),
    )
    canvas = Image.alpha_composite(canvas, shadow.filter(ImageFilter.GaussianBlur(14)))
    canvas.alpha_composite(product, (x, y))
    return canvas.convert("RGB"), (x, y, x + product.width, y + product.height)
