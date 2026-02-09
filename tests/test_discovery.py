"""Tests for deck discovery: scanning directory tree and building index."""

import json
from pathlib import Path

import pytest

from scripts.discovery import discover_decks, deck_id_to_filename
from scripts.schema import DeckNode, DeckTreeIndex


@pytest.fixture
def decks_dir(tmp_path: Path) -> Path:
    """Create a temporary decks directory structure for testing."""
    return tmp_path / "decks"


def _make_image(path: Path) -> None:
    """Create a fake image file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"fake image data")


class TestDiscoverDecks:
    def test_single_flat_deck(self, decks_dir: Path):
        _make_image(decks_dir / "touch" / "img1.jpg")
        _make_image(decks_dir / "touch" / "img2.jpg")

        index = discover_decks(decks_dir)
        assert len(index.decks) == 1
        assert index.decks[0].id == "touch"
        assert index.decks[0].name == "Touch"
        assert index.decks[0].is_leaf is True
        assert index.decks[0].data_file is not None

    def test_multiple_flat_decks(self, decks_dir: Path):
        _make_image(decks_dir / "touch" / "img1.jpg")
        _make_image(decks_dir / "unsure" / "img1.jpeg")

        index = discover_decks(decks_dir)
        assert len(index.decks) == 2
        ids = {d.id for d in index.decks}
        assert ids == {"touch", "unsure"}

    def test_nested_decks(self, decks_dir: Path):
        _make_image(decks_dir / "emotional" / "connection" / "card.jpg")
        _make_image(decks_dir / "emotional" / "confession" / "card.jpg")

        index = discover_decks(decks_dir)
        assert len(index.decks) == 1
        emotional = index.decks[0]
        assert emotional.id == "emotional"
        assert emotional.is_leaf is False
        assert emotional.children is not None
        assert len(emotional.children) == 2
        child_ids = {c.id for c in emotional.children}
        assert child_ids == {"emotional/connection", "emotional/confession"}

    def test_hybrid_node(self, decks_dir: Path):
        """A dir with both images and child dirs."""
        _make_image(decks_dir / "emotional" / "sheet1.jpg")
        _make_image(decks_dir / "emotional" / "connection" / "card.jpg")

        index = discover_decks(decks_dir)
        emotional = index.decks[0]
        assert emotional.is_leaf is True
        assert emotional.data_file is not None
        assert emotional.children is not None
        assert len(emotional.children) == 1

    def test_empty_dir_ignored(self, decks_dir: Path):
        (decks_dir / "mastery").mkdir(parents=True)

        index = discover_decks(decks_dir)
        assert len(index.decks) == 0

    def test_nonexistent_dir_returns_empty(self, tmp_path: Path):
        index = discover_decks(tmp_path / "nonexistent")
        assert len(index.decks) == 0

    def test_supported_extensions(self, decks_dir: Path):
        _make_image(decks_dir / "multi" / "a.jpg")
        _make_image(decks_dir / "multi" / "b.jpeg")
        _make_image(decks_dir / "multi" / "c.png")
        _make_image(decks_dir / "multi" / "d.heic")
        _make_image(decks_dir / "multi" / "e.HEIC")
        (decks_dir / "multi" / "readme.txt").write_text("not an image")

        index = discover_decks(decks_dir)
        assert len(index.decks) == 1
        assert index.decks[0].is_leaf is True

    def test_deeply_nested(self, decks_dir: Path):
        _make_image(decks_dir / "a" / "b" / "c" / "card.jpg")

        index = discover_decks(decks_dir)
        assert len(index.decks) == 1
        a = index.decks[0]
        assert a.id == "a"
        assert a.is_leaf is False
        assert a.children is not None
        b = a.children[0]
        assert b.id == "a/b"
        assert b.is_leaf is False
        assert b.children is not None
        c = b.children[0]
        assert c.id == "a/b/c"
        assert c.is_leaf is True

    def test_deck_names_titlecased(self, decks_dir: Path):
        _make_image(decks_dir / "my-cool-deck" / "card.jpg")

        index = discover_decks(decks_dir)
        assert index.decks[0].name == "My Cool Deck"

    def test_index_serialization(self, decks_dir: Path):
        _make_image(decks_dir / "touch" / "img.jpg")
        _make_image(decks_dir / "emotional" / "connection" / "img.jpg")

        index = discover_decks(decks_dir)
        json_str = index.model_dump_json()
        restored = DeckTreeIndex.model_validate(json.loads(json_str))
        assert restored == index

    def test_sorted_alphabetically(self, decks_dir: Path):
        _make_image(decks_dir / "zebra" / "img.jpg")
        _make_image(decks_dir / "alpha" / "img.jpg")
        _make_image(decks_dir / "mid" / "img.jpg")

        index = discover_decks(decks_dir)
        names = [d.id for d in index.decks]
        assert names == ["alpha", "mid", "zebra"]


class TestDeckIdToFilename:
    def test_simple(self):
        assert deck_id_to_filename("touch") == "decks/touch.json"

    def test_nested(self):
        assert deck_id_to_filename("emotional/connection") == "decks/emotional--connection.json"

    def test_deeply_nested(self):
        assert deck_id_to_filename("a/b/c") == "decks/a--b--c.json"
