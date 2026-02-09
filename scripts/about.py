"""About text extraction and generation for decks."""

from pathlib import Path
from typing import Callable

from scripts.translation import detect_language

# Provider that generates an about summary from card texts.
# Takes (card_texts, language) and returns a summary string.
AboutGenerator = Callable[[list[str], str], str]

# Provider that translates text. Takes (text, target_lang) and returns translation.
TranslateFunc = Callable[[str, str], str]

DEFAULT_ABOUT = "A collection of cards for reflection and conversation."


def load_about_texts(deck_dir: Path) -> tuple[str | None, str | None]:
    """Load about texts from a deck directory.

    Preference order:
    1. about.en.txt + about.es.txt (bilingual pair)
    2. about.txt (single file, language auto-detected)

    Returns (english_text, spanish_text). Either or both may be None.
    """
    en_path = deck_dir / "about.en.txt"
    es_path = deck_dir / "about.es.txt"
    generic_path = deck_dir / "about.txt"

    en_text: str | None = None
    es_text: str | None = None

    if en_path.exists():
        en_text = en_path.read_text(encoding="utf-8").strip()
    if es_path.exists():
        es_text = es_path.read_text(encoding="utf-8").strip()

    if en_text is None and es_text is None and generic_path.exists():
        text = generic_path.read_text(encoding="utf-8").strip()
        lang = detect_language([text])
        if lang == "es":
            es_text = text
        else:
            en_text = text

    return en_text, es_text


def generate_about_text(
    card_texts: list[str],
    language: str,
    provider: AboutGenerator,
) -> str:
    """Generate an about summary from card texts.

    Returns a summary in the given language.
    """
    if not card_texts:
        return DEFAULT_ABOUT
    return provider(card_texts, language)


def resolve_about(
    deck_dir: Path,
    card_texts: list[str],
    source_lang: str,
    translate: TranslateFunc,
    generate: AboutGenerator,
) -> tuple[str, str]:
    """Resolve about text for a deck, ensuring both EN and ES versions.

    1. Try loading from files.
    2. If only one language is found, translate the other.
    3. If none found, generate from card texts and translate.

    Returns (english_text, spanish_text).
    """
    en, es = load_about_texts(deck_dir)

    if en is not None and es is not None:
        return en, es

    if en is not None and es is None:
        es = translate(en, "es")
        return en, es

    if es is not None and en is None:
        en = translate(es, "en")
        return en, es

    # Neither found: generate
    generated = generate_about_text(card_texts, source_lang, generate)
    if source_lang == "en":
        en = generated
        es = translate(generated, "es")
    else:
        es = generated
        en = translate(generated, "en")

    return en, es
