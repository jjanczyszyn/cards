"""Tests for manifest fingerprinting and staleness detection."""

import json
from pathlib import Path

import pytest

from scripts.manifest import (
    compute_deck_fingerprint,
    generate_manifest,
    check_staleness,
    StalenessResult,
)
from scripts.schema import DeckManifest


def _make_image(path: Path, content: bytes = b"fake image data") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


class TestComputeDeckFingerprint:
    def test_fingerprint_is_hex_string(self, tmp_path: Path):
        deck_dir = tmp_path / "deck"
        _make_image(deck_dir / "img1.jpg")
        fp = compute_deck_fingerprint(deck_dir)
        assert isinstance(fp, str)
        assert len(fp) == 64  # SHA-256 hex digest

    def test_same_content_same_fingerprint(self, tmp_path: Path):
        d1 = tmp_path / "d1"
        d2 = tmp_path / "d2"
        _make_image(d1 / "img.jpg", b"same content")
        _make_image(d2 / "img.jpg", b"same content")
        assert compute_deck_fingerprint(d1) == compute_deck_fingerprint(d2)

    def test_different_content_different_fingerprint(self, tmp_path: Path):
        d1 = tmp_path / "d1"
        d2 = tmp_path / "d2"
        _make_image(d1 / "img.jpg", b"content A")
        _make_image(d2 / "img.jpg", b"content B")
        assert compute_deck_fingerprint(d1) != compute_deck_fingerprint(d2)

    def test_additional_file_changes_fingerprint(self, tmp_path: Path):
        deck_dir = tmp_path / "deck"
        _make_image(deck_dir / "img1.jpg", b"data")
        fp1 = compute_deck_fingerprint(deck_dir)
        _make_image(deck_dir / "img2.jpg", b"more data")
        fp2 = compute_deck_fingerprint(deck_dir)
        assert fp1 != fp2

    def test_config_file_included_in_fingerprint(self, tmp_path: Path):
        deck_dir = tmp_path / "deck"
        _make_image(deck_dir / "img.jpg", b"data")
        fp1 = compute_deck_fingerprint(deck_dir)
        (deck_dir / "deck.config.json").write_text('{"grid": [2, 3]}')
        fp2 = compute_deck_fingerprint(deck_dir)
        assert fp1 != fp2

    def test_non_image_files_excluded(self, tmp_path: Path):
        deck_dir = tmp_path / "deck"
        _make_image(deck_dir / "img.jpg", b"data")
        fp1 = compute_deck_fingerprint(deck_dir)
        (deck_dir / "notes.md").write_text("some notes")
        fp2 = compute_deck_fingerprint(deck_dir)
        # notes.md is not an image or config, should not affect fingerprint
        assert fp1 == fp2

    def test_about_files_included_in_fingerprint(self, tmp_path: Path):
        deck_dir = tmp_path / "deck"
        _make_image(deck_dir / "img.jpg", b"data")
        fp1 = compute_deck_fingerprint(deck_dir)
        (deck_dir / "about.en.txt").write_text("About this deck")
        fp2 = compute_deck_fingerprint(deck_dir)
        assert fp1 != fp2


class TestGenerateManifest:
    def test_generates_entries_for_leaf_decks(self, tmp_path: Path):
        decks_dir = tmp_path / "decks"
        _make_image(decks_dir / "touch" / "img.jpg")
        _make_image(decks_dir / "unsure" / "img.jpg")

        manifest = generate_manifest(decks_dir)
        assert len(manifest.entries) == 2
        ids = {e.deck_id for e in manifest.entries}
        assert ids == {"touch", "unsure"}

    def test_nested_deck_entries(self, tmp_path: Path):
        decks_dir = tmp_path / "decks"
        _make_image(decks_dir / "emotional" / "connection" / "img.jpg")

        manifest = generate_manifest(decks_dir)
        assert len(manifest.entries) == 1
        assert manifest.entries[0].deck_id == "emotional/connection"

    def test_manifest_serialization(self, tmp_path: Path):
        decks_dir = tmp_path / "decks"
        _make_image(decks_dir / "touch" / "img.jpg")

        manifest = generate_manifest(decks_dir)
        json_str = manifest.model_dump_json()
        restored = DeckManifest.model_validate(json.loads(json_str))
        assert restored == manifest


class TestCheckStaleness:
    def test_no_stale_decks(self, tmp_path: Path):
        decks_dir = tmp_path / "decks"
        data_dir = tmp_path / "data"
        _make_image(decks_dir / "touch" / "img.jpg")

        # Generate manifest and write it
        manifest = generate_manifest(decks_dir)
        data_dir.mkdir(parents=True)
        (data_dir / "deck-manifest.json").write_text(manifest.model_dump_json())
        # Write dummy deck data files
        (data_dir / "decks").mkdir()
        (data_dir / "decks" / "touch.json").write_text("{}")

        result = check_staleness(decks_dir, data_dir)
        assert result.is_fresh
        assert not result.new_decks
        assert not result.changed_decks
        assert not result.removed_decks

    def test_new_deck_detected(self, tmp_path: Path):
        decks_dir = tmp_path / "decks"
        data_dir = tmp_path / "data"
        _make_image(decks_dir / "touch" / "img.jpg")

        # Empty manifest
        data_dir.mkdir(parents=True)
        empty = DeckManifest(entries=[])
        (data_dir / "deck-manifest.json").write_text(empty.model_dump_json())

        result = check_staleness(decks_dir, data_dir)
        assert not result.is_fresh
        assert "touch" in result.new_decks

    def test_changed_deck_detected(self, tmp_path: Path):
        decks_dir = tmp_path / "decks"
        data_dir = tmp_path / "data"
        _make_image(decks_dir / "touch" / "img.jpg", b"original")

        manifest = generate_manifest(decks_dir)
        data_dir.mkdir(parents=True)
        (data_dir / "deck-manifest.json").write_text(manifest.model_dump_json())
        (data_dir / "decks").mkdir()
        (data_dir / "decks" / "touch.json").write_text("{}")

        # Change the image
        _make_image(decks_dir / "touch" / "img.jpg", b"modified")

        result = check_staleness(decks_dir, data_dir)
        assert not result.is_fresh
        assert "touch" in result.changed_decks

    def test_removed_deck_detected(self, tmp_path: Path):
        decks_dir = tmp_path / "decks"
        data_dir = tmp_path / "data"
        _make_image(decks_dir / "touch" / "img.jpg")

        manifest = generate_manifest(decks_dir)
        data_dir.mkdir(parents=True)
        (data_dir / "deck-manifest.json").write_text(manifest.model_dump_json())
        (data_dir / "decks").mkdir()
        (data_dir / "decks" / "touch.json").write_text("{}")

        # Remove the deck directory
        import shutil
        shutil.rmtree(decks_dir / "touch")

        result = check_staleness(decks_dir, data_dir)
        assert not result.is_fresh
        assert "touch" in result.removed_decks

    def test_missing_manifest_all_new(self, tmp_path: Path):
        decks_dir = tmp_path / "decks"
        data_dir = tmp_path / "data"
        _make_image(decks_dir / "touch" / "img.jpg")
        data_dir.mkdir(parents=True)

        result = check_staleness(decks_dir, data_dir)
        assert not result.is_fresh
        assert "touch" in result.new_decks

    def test_missing_data_file_is_stale(self, tmp_path: Path):
        decks_dir = tmp_path / "decks"
        data_dir = tmp_path / "data"
        _make_image(decks_dir / "touch" / "img.jpg")

        manifest = generate_manifest(decks_dir)
        data_dir.mkdir(parents=True)
        (data_dir / "deck-manifest.json").write_text(manifest.model_dump_json())
        # Do NOT write the deck data file

        result = check_staleness(decks_dir, data_dir)
        assert not result.is_fresh
        assert "touch" in result.missing_data_files
