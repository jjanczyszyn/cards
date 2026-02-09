"""Tests for about text extraction and generation."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scripts.about import (
    load_about_texts,
    generate_about_text,
    resolve_about,
)


class TestLoadAboutTexts:
    def test_prefer_bilingual_files(self, tmp_path: Path):
        (tmp_path / "about.en.txt").write_text("English about")
        (tmp_path / "about.es.txt").write_text("Spanish about")
        en, es = load_about_texts(tmp_path)
        assert en == "English about"
        assert es == "Spanish about"

    def test_about_txt_fallback(self, tmp_path: Path):
        (tmp_path / "about.txt").write_text("Generic about text")
        en, es = load_about_texts(tmp_path)
        # One should be the original text, the other None (needs translation)
        assert en == "Generic about text" or es == "Generic about text"

    def test_no_about_files(self, tmp_path: Path):
        en, es = load_about_texts(tmp_path)
        assert en is None
        assert es is None

    def test_only_en_file(self, tmp_path: Path):
        (tmp_path / "about.en.txt").write_text("Only English")
        en, es = load_about_texts(tmp_path)
        assert en == "Only English"
        assert es is None

    def test_only_es_file(self, tmp_path: Path):
        (tmp_path / "about.es.txt").write_text("Solo espanol")
        en, es = load_about_texts(tmp_path)
        assert en is None
        assert es == "Solo espanol"

    def test_whitespace_stripped(self, tmp_path: Path):
        (tmp_path / "about.en.txt").write_text("  Text with spaces  \n")
        (tmp_path / "about.es.txt").write_text("  Texto con espacios  \n")
        en, es = load_about_texts(tmp_path)
        assert en == "Text with spaces"
        assert es == "Texto con espacios"


class TestGenerateAboutText:
    def test_generates_from_card_texts(self):
        card_texts = ["What makes you happy?", "Describe your dreams", "Tell me a secret"]
        mock_provider = MagicMock(return_value="A deck of introspective questions")
        result = generate_about_text(card_texts, "en", mock_provider)
        assert result == "A deck of introspective questions"
        mock_provider.assert_called_once()

    def test_empty_cards_returns_default(self):
        mock_provider = MagicMock()
        result = generate_about_text([], "en", mock_provider)
        assert result is not None
        assert len(result) > 0
        mock_provider.assert_not_called()


class TestResolveAbout:
    def test_both_present(self, tmp_path: Path):
        (tmp_path / "about.en.txt").write_text("English")
        (tmp_path / "about.es.txt").write_text("Spanish")
        mock_translate = MagicMock()
        mock_generate = MagicMock()

        en, es = resolve_about(tmp_path, [], "en", mock_translate, mock_generate)
        assert en == "English"
        assert es == "Spanish"
        mock_translate.assert_not_called()
        mock_generate.assert_not_called()

    def test_only_en_triggers_translation(self, tmp_path: Path):
        (tmp_path / "about.en.txt").write_text("English only")
        mock_translate = MagicMock(return_value="Traducido")
        mock_generate = MagicMock()

        en, es = resolve_about(tmp_path, [], "en", mock_translate, mock_generate)
        assert en == "English only"
        assert es == "Traducido"
        mock_translate.assert_called_once_with("English only", "es")

    def test_only_es_triggers_translation(self, tmp_path: Path):
        (tmp_path / "about.es.txt").write_text("Solo espanol")
        mock_translate = MagicMock(return_value="Translated")
        mock_generate = MagicMock()

        en, es = resolve_about(tmp_path, [], "es", mock_translate, mock_generate)
        assert en == "Translated"
        assert es == "Solo espanol"
        mock_translate.assert_called_once_with("Solo espanol", "en")

    def test_no_files_triggers_generation(self, tmp_path: Path):
        mock_translate = MagicMock(return_value="Traducido")
        mock_generate = MagicMock(return_value="Generated about")

        card_texts = ["Card 1", "Card 2"]
        en, es = resolve_about(tmp_path, card_texts, "en", mock_translate, mock_generate)
        assert en == "Generated about"
        assert es == "Traducido"
        mock_generate.assert_called_once()
        mock_translate.assert_called_once_with("Generated about", "es")
