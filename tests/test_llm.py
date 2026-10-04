import pytest
from PIL import Image

from adgen.core.llm import find_data_uris, fit_to_max_edge, parse_json_object


def test_parse_json_object_strips_fences_and_prose():
    assert parse_json_object('Here you go:\n```json\n{"a": 1}\n```') == {"a": 1}


def test_parse_json_object_repairs_trailing_commas():
    assert parse_json_object('{"a": [1, 2,], "b": {"c": 3,},}') == {"a": [1, 2], "b": {"c": 3}}


def test_parse_json_object_rejects_non_json():
    with pytest.raises(ValueError):
        parse_json_object("no braces here")


def test_find_data_uris_walks_nested_response():
    body = {"choices": [{"message": {"images": [{"image_url": {"url": "data:image/png;base64,QUJD"}}]}}]}
    assert find_data_uris(body) == ["QUJD"]


def test_fit_to_max_edge_downscales_keeping_ratio():
    resized = fit_to_max_edge(Image.new("RGB", (2048, 1024)))
    assert resized.size == (1024, 512)


def test_fit_to_max_edge_leaves_small_images_untouched():
    image = Image.new("RGB", (1024, 1024))
    assert fit_to_max_edge(image) is image
