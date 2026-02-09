"""Deck discovery: scan directory tree and build deck index."""

from pathlib import Path

from scripts.schema import DeckNode, DeckTreeIndex

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic"}


def deck_id_to_filename(deck_id: str) -> str:
    """Convert a deck id (path-like) to a JSON filename."""
    return "decks/" + deck_id.replace("/", "--") + ".json"


def _dir_name_to_display(name: str) -> str:
    """Convert a directory name to a display name."""
    return name.replace("-", " ").replace("_", " ").title()


def _has_images(directory: Path) -> bool:
    """Check if a directory directly contains any supported image files."""
    for f in directory.iterdir():
        if f.is_file() and f.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
            return True
    return False


def _build_tree(directory: Path, base_path: Path) -> DeckNode | None:
    """Recursively build a DeckNode from a directory.

    Returns None if the directory (and all descendants) contain no images.
    """
    if not directory.is_dir():
        return None

    rel = directory.relative_to(base_path)
    deck_id = str(rel).replace("\\", "/")  # normalize Windows paths
    display_name = _dir_name_to_display(directory.name)

    has_own_images = _has_images(directory)

    children: list[DeckNode] = []
    for child in sorted(directory.iterdir()):
        if child.is_dir():
            child_node = _build_tree(child, base_path)
            if child_node is not None:
                children.append(child_node)

    if not has_own_images and not children:
        return None

    return DeckNode(
        id=deck_id,
        name=display_name,
        is_leaf=has_own_images,
        data_file=deck_id_to_filename(deck_id) if has_own_images else None,
        children=children if children else None,
    )


def discover_decks(decks_dir: Path) -> DeckTreeIndex:
    """Discover all decks under the given directory and return a DeckTreeIndex."""
    if not decks_dir.is_dir():
        return DeckTreeIndex(decks=[])

    top_level: list[DeckNode] = []
    for entry in sorted(decks_dir.iterdir()):
        if entry.is_dir():
            node = _build_tree(entry, decks_dir)
            if node is not None:
                top_level.append(node)

    return DeckTreeIndex(decks=top_level)
