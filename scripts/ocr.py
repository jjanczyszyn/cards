"""OCR module with content-hash caching."""

import hashlib
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable

from PIL import Image

from scripts.segmentation import BBox


@dataclass
class OCRResult:
    """Result of OCR on a card crop."""
    text: str
    confidence: float


# Type alias for OCR provider functions.
# A provider takes a PIL Image and returns an OCRResult.
OCRProvider = Callable[[Image.Image], OCRResult]


class OCRCache:
    """File-based cache for OCR results, keyed by content hash."""

    def __init__(self, cache_dir: Path) -> None:
        self._dir = cache_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self._dir / f"{key}.json"

    def get(self, key: str) -> OCRResult | None:
        path = self._path(key)
        if not path.exists():
            return None
        data = json.loads(path.read_text())
        return OCRResult(text=data["text"], confidence=data["confidence"])

    def put(self, key: str, result: OCRResult) -> None:
        path = self._path(key)
        path.write_text(json.dumps(asdict(result)))


def compute_crop_hash(image_path: Path, bbox: BBox) -> str:
    """Compute a hash uniquely identifying a card crop.

    Based on the image file content and the bounding box.
    """
    h = hashlib.sha256()
    h.update(image_path.read_bytes())
    h.update(f"{bbox.x},{bbox.y},{bbox.w},{bbox.h}".encode())
    return h.hexdigest()


def _crop_image(image_path: Path, bbox: BBox) -> Image.Image:
    """Crop a region from an image."""
    with Image.open(image_path) as img:
        return img.crop((bbox.x, bbox.y, bbox.x + bbox.w, bbox.y + bbox.h))


def ocr_card_crop(
    image_path: Path,
    bbox: BBox,
    cache: OCRCache,
    provider: OCRProvider,
) -> OCRResult:
    """OCR a card crop, using cache if available.

    Args:
        image_path: Path to the sheet image.
        bbox: Bounding box of the card within the sheet.
        cache: OCR cache instance.
        provider: OCR provider function to call on cache miss.
    """
    crop_hash = compute_crop_hash(image_path, bbox)

    cached = cache.get(crop_hash)
    if cached is not None:
        return cached

    crop = _crop_image(image_path, bbox)
    result = provider(crop)
    cache.put(crop_hash, result)
    return result
