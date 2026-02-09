"""Tests for color and symbol classification."""

from pathlib import Path

import pytest
from PIL import Image

from scripts.classification import (
    classify_color,
    COLOR_PALETTE,
)


def _make_solid_image(path: Path, color: tuple[int, int, int], size: tuple[int, int] = (100, 100)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", size, color=color)
    img.save(str(path))


class TestClassifyColor:
    def test_red_card(self, tmp_path: Path):
        img = Image.new("RGB", (100, 100), color=(220, 30, 30))
        assert classify_color(img) == "red"

    def test_blue_card(self, tmp_path: Path):
        img = Image.new("RGB", (100, 100), color=(30, 30, 220))
        assert classify_color(img) == "blue"

    def test_green_card(self, tmp_path: Path):
        img = Image.new("RGB", (100, 100), color=(30, 180, 30))
        assert classify_color(img) == "green"

    def test_yellow_card(self, tmp_path: Path):
        img = Image.new("RGB", (100, 100), color=(230, 230, 30))
        assert classify_color(img) == "yellow"

    def test_purple_card(self, tmp_path: Path):
        img = Image.new("RGB", (100, 100), color=(150, 30, 200))
        assert classify_color(img) == "purple"

    def test_orange_card(self, tmp_path: Path):
        img = Image.new("RGB", (100, 100), color=(240, 140, 20))
        assert classify_color(img) == "orange"

    def test_white_card(self, tmp_path: Path):
        img = Image.new("RGB", (100, 100), color=(250, 250, 250))
        assert classify_color(img) == "white"

    def test_black_card(self, tmp_path: Path):
        img = Image.new("RGB", (100, 100), color=(15, 15, 15))
        assert classify_color(img) == "black"

    def test_palette_has_expected_colors(self):
        expected = {"red", "blue", "green", "yellow", "purple", "orange", "white", "black", "pink"}
        assert expected.issubset(set(COLOR_PALETTE.keys()))

    def test_classify_returns_string(self):
        img = Image.new("RGB", (50, 50), color=(128, 128, 128))
        result = classify_color(img)
        assert isinstance(result, str)
        assert result in COLOR_PALETTE
