"""Card segmentation: split sheet images into individual card regions."""

import json
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


class SegmentationError(Exception):
    """Raised when automatic segmentation fails."""
    pass


@dataclass(frozen=True)
class BBox:
    """Bounding box for a card region (x, y, width, height)."""
    x: int
    y: int
    w: int
    h: int


@dataclass
class DeckConfig:
    """Configuration for card segmentation loaded from deck.config.json."""
    grid: tuple[int, int] | None = None  # (rows, cols)
    bboxes: list[BBox] | None = None
    symbol_roi: tuple[int, int, int, int] | None = None  # (x, y, w, h)


def load_deck_config(deck_dir: Path) -> DeckConfig | None:
    """Load deck.config.json from a deck directory if it exists."""
    config_path = deck_dir / "deck.config.json"
    if not config_path.exists():
        return None

    raw = json.loads(config_path.read_text())
    config = DeckConfig()

    if "grid" in raw:
        rows, cols = raw["grid"]
        config.grid = (int(rows), int(cols))

    if "bboxes" in raw:
        config.bboxes = [
            BBox(x=int(b[0]), y=int(b[1]), w=int(b[2]), h=int(b[3]))
            for b in raw["bboxes"]
        ]

    if "symbolRoi" in raw:
        r = raw["symbolRoi"]
        config.symbol_roi = (int(r[0]), int(r[1]), int(r[2]), int(r[3]))

    return config


def compute_grid_bboxes(rows: int, cols: int, width: int, height: int) -> list[BBox]:
    """Compute bounding boxes for a regular grid layout."""
    cell_w = width // cols
    cell_h = height // rows
    bboxes: list[BBox] = []
    for row in range(rows):
        for col in range(cols):
            bboxes.append(BBox(
                x=col * cell_w,
                y=row * cell_h,
                w=cell_w,
                h=cell_h,
            ))
    return bboxes


def _get_image_dimensions(image_path: Path) -> tuple[int, int]:
    """Get image width and height."""
    with Image.open(image_path) as img:
        return img.size  # (width, height)


def segment_sheet(image_path: Path, deck_dir: Path) -> list[BBox]:
    """Segment a sheet image into card bounding boxes.

    Uses config if available, otherwise attempts heuristic segmentation.
    """
    config = load_deck_config(deck_dir)

    if config and config.bboxes:
        return config.bboxes

    if config and config.grid:
        rows, cols = config.grid
        width, height = _get_image_dimensions(image_path)
        return compute_grid_bboxes(rows, cols, width, height)

    # Heuristic fallback - not yet implemented
    raise SegmentationError(
        f"Could not automatically segment '{image_path.name}'. "
        f"Please provide a deck.config.json in '{deck_dir}' with either "
        f"a 'grid' (e.g. [3, 3]) or explicit 'bboxes' definitions."
    )
