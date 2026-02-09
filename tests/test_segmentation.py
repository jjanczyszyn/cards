"""Tests for card segmentation from sheet images."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.segmentation import (
    BBox,
    DeckConfig,
    load_deck_config,
    compute_grid_bboxes,
    segment_sheet,
    SegmentationError,
)


class TestDeckConfig:
    def test_load_grid_config(self, tmp_path: Path):
        config_path = tmp_path / "deck.config.json"
        config_path.write_text(json.dumps({"grid": [3, 3]}))
        config = load_deck_config(tmp_path)
        assert config is not None
        assert config.grid == (3, 3)

    def test_load_bboxes_config(self, tmp_path: Path):
        config_path = tmp_path / "deck.config.json"
        config_path.write_text(json.dumps({
            "bboxes": [[0, 0, 100, 100], [100, 0, 200, 100]]
        }))
        config = load_deck_config(tmp_path)
        assert config is not None
        assert config.bboxes is not None
        assert len(config.bboxes) == 2

    def test_no_config_returns_none(self, tmp_path: Path):
        config = load_deck_config(tmp_path)
        assert config is None

    def test_config_with_symbol_roi(self, tmp_path: Path):
        config_path = tmp_path / "deck.config.json"
        config_path.write_text(json.dumps({
            "grid": [2, 2],
            "symbolRoi": [10, 10, 50, 50]
        }))
        config = load_deck_config(tmp_path)
        assert config is not None
        assert config.symbol_roi == (10, 10, 50, 50)


class TestComputeGridBboxes:
    def test_2x2_grid(self):
        bboxes = compute_grid_bboxes(rows=2, cols=2, width=200, height=200)
        assert len(bboxes) == 4
        assert bboxes[0] == BBox(x=0, y=0, w=100, h=100)
        assert bboxes[1] == BBox(x=100, y=0, w=100, h=100)
        assert bboxes[2] == BBox(x=0, y=100, w=100, h=100)
        assert bboxes[3] == BBox(x=100, y=100, w=100, h=100)

    def test_3x3_grid(self):
        bboxes = compute_grid_bboxes(rows=3, cols=3, width=300, height=300)
        assert len(bboxes) == 9
        assert bboxes[0] == BBox(x=0, y=0, w=100, h=100)
        assert bboxes[8] == BBox(x=200, y=200, w=100, h=100)

    def test_1x1_grid(self):
        bboxes = compute_grid_bboxes(rows=1, cols=1, width=500, height=300)
        assert len(bboxes) == 1
        assert bboxes[0] == BBox(x=0, y=0, w=500, h=300)

    def test_non_even_division(self):
        bboxes = compute_grid_bboxes(rows=2, cols=3, width=301, height=201)
        assert len(bboxes) == 6
        # Each cell should be floor division
        assert bboxes[0].w == 100
        assert bboxes[0].h == 100


class TestSegmentSheet:
    def _make_test_image(self, path: Path, width: int = 200, height: int = 200) -> None:
        """Create a minimal valid image file for testing."""
        # Create a simple BMP file (easiest to construct without PIL)
        # BMP header for a small image
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            from PIL import Image
            img = Image.new("RGB", (width, height), color=(255, 255, 255))
            img.save(str(path))
        except ImportError:
            # If PIL not available, write dummy bytes and mock image loading
            path.write_bytes(b"fake image")

    def test_segment_with_grid_config(self, tmp_path: Path):
        config_path = tmp_path / "deck.config.json"
        config_path.write_text(json.dumps({"grid": [2, 2]}))
        img_path = tmp_path / "sheet.jpg"
        self._make_test_image(img_path, 200, 200)

        bboxes = segment_sheet(img_path, tmp_path)
        assert len(bboxes) == 4

    def test_segment_with_explicit_bboxes(self, tmp_path: Path):
        config_path = tmp_path / "deck.config.json"
        config_path.write_text(json.dumps({
            "bboxes": [[0, 0, 100, 100], [100, 0, 200, 100]]
        }))
        img_path = tmp_path / "sheet.jpg"
        self._make_test_image(img_path)

        bboxes = segment_sheet(img_path, tmp_path)
        assert len(bboxes) == 2
        assert bboxes[0] == BBox(x=0, y=0, w=100, h=100)

    def test_segment_no_config_uses_heuristic(self, tmp_path: Path):
        img_path = tmp_path / "sheet.jpg"
        self._make_test_image(img_path)

        # Heuristic is a stub that raises SegmentationError for now
        with pytest.raises(SegmentationError, match="provide a deck.config.json"):
            segment_sheet(img_path, tmp_path)
