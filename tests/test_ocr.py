"""Tests for OCR module with content-hash caching."""

import hashlib
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.ocr import (
    OCRCache,
    OCRResult,
    ocr_card_crop,
    compute_crop_hash,
)
from scripts.segmentation import BBox


def _make_test_image(path: Path, width: int = 100, height: int = 100) -> None:
    from PIL import Image
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (width, height), color=(200, 200, 200))
    img.save(str(path))


class TestComputeCropHash:
    def test_returns_hex_string(self, tmp_path: Path):
        img_path = tmp_path / "img.jpg"
        _make_test_image(img_path, 200, 200)
        bbox = BBox(x=0, y=0, w=100, h=100)
        h = compute_crop_hash(img_path, bbox)
        assert isinstance(h, str)
        assert len(h) == 64

    def test_same_crop_same_hash(self, tmp_path: Path):
        img_path = tmp_path / "img.jpg"
        _make_test_image(img_path, 200, 200)
        bbox = BBox(x=0, y=0, w=100, h=100)
        h1 = compute_crop_hash(img_path, bbox)
        h2 = compute_crop_hash(img_path, bbox)
        assert h1 == h2

    def test_different_bbox_different_hash(self, tmp_path: Path):
        img_path = tmp_path / "img.jpg"
        _make_test_image(img_path, 200, 200)
        h1 = compute_crop_hash(img_path, BBox(x=0, y=0, w=100, h=100))
        h2 = compute_crop_hash(img_path, BBox(x=100, y=0, w=100, h=100))
        assert h1 != h2


class TestOCRCache:
    def test_cache_miss(self, tmp_path: Path):
        cache = OCRCache(tmp_path / "cache")
        assert cache.get("abc123") is None

    def test_cache_hit_after_put(self, tmp_path: Path):
        cache = OCRCache(tmp_path / "cache")
        result = OCRResult(text="Hello world", confidence=0.95)
        cache.put("abc123", result)
        got = cache.get("abc123")
        assert got is not None
        assert got.text == "Hello world"
        assert got.confidence == 0.95

    def test_cache_persists_across_instances(self, tmp_path: Path):
        cache_dir = tmp_path / "cache"
        cache1 = OCRCache(cache_dir)
        cache1.put("key1", OCRResult(text="Persisted", confidence=0.9))
        cache2 = OCRCache(cache_dir)
        got = cache2.get("key1")
        assert got is not None
        assert got.text == "Persisted"

    def test_cache_different_keys_independent(self, tmp_path: Path):
        cache = OCRCache(tmp_path / "cache")
        cache.put("key1", OCRResult(text="A", confidence=0.9))
        cache.put("key2", OCRResult(text="B", confidence=0.8))
        assert cache.get("key1").text == "A"
        assert cache.get("key2").text == "B"


class TestOcrCardCrop:
    def test_uses_cache_on_hit(self, tmp_path: Path):
        img_path = tmp_path / "img.jpg"
        _make_test_image(img_path, 200, 200)
        bbox = BBox(x=0, y=0, w=100, h=100)
        cache = OCRCache(tmp_path / "cache")
        crop_hash = compute_crop_hash(img_path, bbox)
        cache.put(crop_hash, OCRResult(text="Cached text", confidence=0.99))

        mock_provider = MagicMock(return_value=OCRResult(text="Fresh OCR", confidence=0.8))
        result = ocr_card_crop(img_path, bbox, cache, mock_provider)

        assert result.text == "Cached text"
        mock_provider.assert_not_called()

    def test_calls_provider_on_miss(self, tmp_path: Path):
        img_path = tmp_path / "img.jpg"
        _make_test_image(img_path, 200, 200)
        bbox = BBox(x=0, y=0, w=100, h=100)
        cache = OCRCache(tmp_path / "cache")

        mock_provider = MagicMock(return_value=OCRResult(text="OCR result", confidence=0.85))
        result = ocr_card_crop(img_path, bbox, cache, mock_provider)

        assert result.text == "OCR result"
        mock_provider.assert_called_once()

    def test_provider_result_cached(self, tmp_path: Path):
        img_path = tmp_path / "img.jpg"
        _make_test_image(img_path, 200, 200)
        bbox = BBox(x=0, y=0, w=100, h=100)
        cache = OCRCache(tmp_path / "cache")

        mock_provider = MagicMock(return_value=OCRResult(text="Fresh", confidence=0.85))
        ocr_card_crop(img_path, bbox, cache, mock_provider)

        # Should now be in cache
        crop_hash = compute_crop_hash(img_path, bbox)
        cached = cache.get(crop_hash)
        assert cached is not None
        assert cached.text == "Fresh"
