"""Translation module with caching and language detection."""

import hashlib
import json
from pathlib import Path
from typing import Callable

# Provider type: takes (source_text, target_lang) and returns translated text.
TranslationProvider = Callable[[str, str], str]


class TranslationCache:
    """File-based cache for translations, keyed by (text_hash, target_lang)."""

    def __init__(self, cache_dir: Path) -> None:
        self._dir = cache_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, text_hash: str, target_lang: str) -> Path:
        return self._dir / f"{text_hash}_{target_lang}.txt"

    def get(self, text_hash: str, target_lang: str) -> str | None:
        path = self._path(text_hash, target_lang)
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def put(self, text_hash: str, target_lang: str, translated: str) -> None:
        path = self._path(text_hash, target_lang)
        path.write_text(translated, encoding="utf-8")


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


# Simple heuristic: Spanish-common characters and words
_SPANISH_INDICATORS = {
    "que", "de", "el", "la", "los", "las", "un", "una", "es", "en",
    "por", "con", "para", "como", "tu", "te", "mi", "su", "nos",
}


def detect_language(samples: list[str]) -> str:
    """Detect whether card text samples are primarily English or Spanish.

    Uses a simple word-frequency heuristic. Returns 'en' or 'es'.
    """
    if not samples:
        return "en"

    spanish_score = 0
    total_words = 0

    for sample in samples:
        words = sample.lower().split()
        for word in words:
            clean = word.strip(".,;:!?()\"'")
            total_words += 1
            if clean in _SPANISH_INDICATORS:
                spanish_score += 1

    if total_words == 0:
        return "en"

    # If more than 15% of words are Spanish indicators, classify as Spanish
    if spanish_score / total_words > 0.15:
        return "es"

    return "en"


def translate_text(
    text: str,
    target_lang: str,
    cache: TranslationCache,
    provider: TranslationProvider,
) -> str:
    """Translate text to target language, using cache if available."""
    th = _text_hash(text)
    cached = cache.get(th, target_lang)
    if cached is not None:
        return cached

    translated = provider(text, target_lang)
    cache.put(th, target_lang, translated)
    return translated


def ensure_bilingual(
    text: str,
    source_lang: str,
    cache: TranslationCache,
    provider: TranslationProvider,
) -> tuple[str, str]:
    """Ensure text exists in both English and Spanish.

    Returns (english_text, spanish_text).
    """
    if source_lang == "en":
        translated = translate_text(text, "es", cache, provider)
        return text, translated
    else:
        translated = translate_text(text, "en", cache, provider)
        return translated, text
