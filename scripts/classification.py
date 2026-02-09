"""Color and symbol classification for card crops."""

import colorsys

from PIL import Image

# Named color palette: maps color name to representative (H, S, V) ranges.
# H is 0-360, S and V are 0-100.
COLOR_PALETTE: dict[str, tuple[int, int, int]] = {
    "red": (0, 80, 70),
    "orange": (30, 80, 70),
    "yellow": (55, 80, 70),
    "green": (120, 70, 60),
    "blue": (230, 70, 60),
    "purple": (280, 60, 55),
    "pink": (330, 60, 70),
    "white": (0, 0, 95),
    "black": (0, 0, 10),
    "gray": (0, 0, 50),
}


def _rgb_to_hsv_360(r: int, g: int, b: int) -> tuple[float, float, float]:
    """Convert RGB (0-255) to HSV with H in 0-360, S and V in 0-100."""
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    return h * 360, s * 100, v * 100


def _dominant_color(img: Image.Image) -> tuple[int, int, int]:
    """Get the dominant RGB color of an image by averaging all pixels."""
    small = img.resize((50, 50))
    rgb = small.convert("RGB")
    pixels = list(rgb.tobytes())
    # Convert flat byte list to (R, G, B) tuples
    pixel_tuples = [(pixels[i], pixels[i + 1], pixels[i + 2]) for i in range(0, len(pixels), 3)]
    if not pixel_tuples:
        return (128, 128, 128)
    r = sum(p[0] for p in pixel_tuples) // len(pixel_tuples)
    g = sum(p[1] for p in pixel_tuples) // len(pixel_tuples)
    b = sum(p[2] for p in pixel_tuples) // len(pixel_tuples)
    return (r, g, b)


def _hsv_distance(h1: float, s1: float, v1: float, h2: float, s2: float, v2: float) -> float:
    """Compute distance between two HSV colors, accounting for hue wrapping."""
    # Handle achromatic colors (low saturation)
    if s1 < 15 or s2 < 15:
        # For near-gray colors, mostly compare value
        return abs(v1 - v2) + abs(s1 - s2) * 0.5

    # Hue distance (circular)
    hue_diff = abs(h1 - h2)
    if hue_diff > 180:
        hue_diff = 360 - hue_diff

    return hue_diff * 1.0 + abs(s1 - s2) * 0.5 + abs(v1 - v2) * 0.3


def classify_color(img: Image.Image) -> str:
    """Classify the dominant color of an image into a named palette color."""
    r, g, b = _dominant_color(img)
    h, s, v = _rgb_to_hsv_360(r, g, b)

    best_name = "gray"
    best_dist = float("inf")

    for name, (ph, ps, pv) in COLOR_PALETTE.items():
        d = _hsv_distance(h, s, v, ph, ps, pv)
        if d < best_dist:
            best_dist = d
            best_name = name

    return best_name
