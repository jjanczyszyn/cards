"""Tests for translation module with caching."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scripts.translation import (
    TranslationCache,
    detect_language,
    translate_text,
    ensure_bilingual,
)


class TestTranslationCache:
    def test_cache_miss(self, tmp_path: Path):
        cache = TranslationCache(tmp_path / "cache")
        assert cache.get("abc", "es") is None

    def test_cache_hit_after_put(self, tmp_path: Path):
        cache = TranslationCache(tmp_path / "cache")
        cache.put("abc", "es", "Hola mundo")
        assert cache.get("abc", "es") == "Hola mundo"

    def test_different_target_langs_independent(self, tmp_path: Path):
        cache = TranslationCache(tmp_path / "cache")
        cache.put("abc", "es", "Spanish")
        cache.put("abc", "en", "English")
        assert cache.get("abc", "es") == "Spanish"
        assert cache.get("abc", "en") == "English"

    def test_cache_persists_across_instances(self, tmp_path: Path):
        cache_dir = tmp_path / "cache"
        c1 = TranslationCache(cache_dir)
        c1.put("hash1", "es", "Persisted")
        c2 = TranslationCache(cache_dir)
        assert c2.get("hash1", "es") == "Persisted"


class TestDetectLanguage:
    def test_detect_english(self):
        samples = [
            "What makes you happy?",
            "Describe your ideal day",
            "Tell me about yourself",
        ]
        assert detect_language(samples) == "en"

    def test_detect_spanish(self):
        samples = [
            "Que te hace feliz?",
            "Describe tu dia ideal",
            "Cuentame sobre ti",
        ]
        assert detect_language(samples) == "es"

    def test_empty_samples_defaults_to_en(self):
        assert detect_language([]) == "en"

    def test_single_sample(self):
        lang = detect_language(["Hello world"])
        assert lang in ("en", "es")


class TestTranslateText:
    def test_translation_with_cache_miss(self, tmp_path: Path):
        cache = TranslationCache(tmp_path / "cache")
        mock_provider = MagicMock(return_value="Hola mundo")

        result = translate_text("Hello world", "es", cache, mock_provider)
        assert result == "Hola mundo"
        mock_provider.assert_called_once_with("Hello world", "es")

    def test_translation_with_cache_hit(self, tmp_path: Path):
        cache = TranslationCache(tmp_path / "cache")
        # Pre-populate cache
        import hashlib
        text_hash = hashlib.sha256("Hello world".encode()).hexdigest()
        cache.put(text_hash, "es", "Cached translation")

        mock_provider = MagicMock()
        result = translate_text("Hello world", "es", cache, mock_provider)
        assert result == "Cached translation"
        mock_provider.assert_not_called()

    def test_translation_result_cached(self, tmp_path: Path):
        cache = TranslationCache(tmp_path / "cache")
        mock_provider = MagicMock(return_value="Translated")

        translate_text("Source text", "es", cache, mock_provider)

        import hashlib
        text_hash = hashlib.sha256("Source text".encode()).hexdigest()
        assert cache.get(text_hash, "es") == "Translated"


class TestEnsureBilingual:
    def test_english_source_adds_spanish(self, tmp_path: Path):
        cache = TranslationCache(tmp_path / "cache")
        mock_provider = MagicMock(return_value="Hola")

        en, es = ensure_bilingual("Hello", "en", cache, mock_provider)
        assert en == "Hello"
        assert es == "Hola"
        mock_provider.assert_called_once_with("Hello", "es")

    def test_spanish_source_adds_english(self, tmp_path: Path):
        cache = TranslationCache(tmp_path / "cache")
        mock_provider = MagicMock(return_value="Hello")

        en, es = ensure_bilingual("Hola", "es", cache, mock_provider)
        assert en == "Hello"
        assert es == "Hola"
        mock_provider.assert_called_once_with("Hola", "en")

    def test_no_translation_when_same_target(self, tmp_path: Path):
        """If source is already bilingual-ready, still translate to other lang."""
        cache = TranslationCache(tmp_path / "cache")
        mock_provider = MagicMock(return_value="Translated")

        en, es = ensure_bilingual("Text", "en", cache, mock_provider)
        assert en == "Text"
        assert es == "Translated"
