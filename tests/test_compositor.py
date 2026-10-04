from PIL import Image, ImageChops, ImageDraw

from adgen.generation.compositor import composite_product, font_family, load_font, overlay_headline, quietest_region, region_box


def busy_top_left() -> Image.Image:
    image = Image.new("RGB", (512, 512), (200, 200, 200))
    draw = ImageDraw.Draw(image)
    for x in range(0, 300, 6):
        draw.line([(x, 0), (x, 170)], fill=(0, 0, 0), width=2)
    return image


def test_font_family_from_typography_hint():
    assert font_family("Bold condensed sans, uppercase") == "condensed"
    assert font_family("refined transitional serif caps") == "serif"
    assert font_family("geometric sans-serif") == "sans"


def test_bundled_fonts_load_at_bold_weight():
    for family in ("sans", "serif", "condensed"):
        assert load_font(family, 32).getlength("Ad") > 0


def test_quietest_region_avoids_busy_area_and_the_product():
    image = busy_top_left()
    assert quietest_region(image) != "top_left"
    assert quietest_region(image, avoid=region_box(image, "top_right")) not in ("top_left", "top_right")


def test_overlay_headline_draws_without_resizing():
    image = Image.new("RGB", (512, 512), (240, 240, 240))
    result = overlay_headline(image, "WINTER-PROOF YOUR SKIN", "serif")
    assert result.size == image.size
    assert ImageChops.difference(result, image).getbbox() is not None


def test_composite_product_stays_inside_the_frame():
    cutout = Image.new("RGBA", (200, 400), (255, 0, 0, 255))
    composed, (left, top, right, bottom) = composite_product(Image.new("RGB", (1024, 1024)), cutout, height_ratio=0.3)
    assert composed.size == (1024, 1024)
    assert 0 <= left < right <= 1024 and 0 <= top < bottom <= 1024
    assert bottom - top <= 0.3 * 1024 + 1
