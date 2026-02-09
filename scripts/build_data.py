"""Build data pipeline: discovers decks, segments, OCRs, translates, outputs JSON.

This is the main entry point for `npm run data:build`.
It processes local deck images and produces JSON artifacts for the website.
"""

import json
import os
import sys
from pathlib import Path

from PIL import Image

from scripts.about import resolve_about
from scripts.classification import classify_color
from scripts.discovery import discover_decks, deck_id_to_filename, SUPPORTED_IMAGE_EXTENSIONS
from scripts.manifest import generate_manifest
from scripts.ocr import OCRCache, OCRResult, ocr_card_crop
from scripts.schema import Card, DeckNode, DeckTreeIndex, LeafDeckData
from scripts.segmentation import BBox, SegmentationError, segment_sheet
from scripts.translation import (
    TranslationCache,
    detect_language,
    ensure_bilingual,
    translate_text,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DECKS_DIR = PROJECT_ROOT / "decks"
DATA_DIR = PROJECT_ROOT / "public" / "data"
CACHE_DIR = PROJECT_ROOT / "data_cache"


def _get_translation_provider():
    """Get the translation provider. Uses Anthropic API if available."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)

            def translate_with_anthropic(text: str, target_lang: str) -> str:
                lang_name = "Spanish" if target_lang == "es" else "English"
                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1024,
                    messages=[{
                        "role": "user",
                        "content": f"Translate the following text to {lang_name}. "
                                   f"Return only the translated text, nothing else.\n\n{text}",
                    }],
                )
                return response.content[0].text

            return translate_with_anthropic
        except ImportError:
            print("Warning: anthropic package not installed, using passthrough translation")

    def passthrough(text: str, target_lang: str) -> str:
        return f"[{target_lang}] {text}"

    return passthrough


def _get_ocr_provider():
    """Get the OCR provider. Uses Anthropic vision API if available."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            import anthropic
            import base64
            import io
            client = anthropic.Anthropic(api_key=api_key)

            def ocr_with_anthropic(img: Image.Image) -> OCRResult:
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                b64 = base64.b64encode(buf.getvalue()).decode()

                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=512,
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": "Read the text on this card. Return only the card text, nothing else. "
                                        "If there is no readable text, return EMPTY.",
                            },
                        ],
                    }],
                )
                text = response.content[0].text.strip()
                if text == "EMPTY":
                    text = ""
                return OCRResult(text=text, confidence=0.9)

            return ocr_with_anthropic
        except ImportError:
            print("Warning: anthropic package not installed, using stub OCR")

    def stub_ocr(img: Image.Image) -> OCRResult:
        return OCRResult(text="[OCR not available]", confidence=0.0)

    return stub_ocr


def _get_about_generator():
    """Get the about text generator. Uses Anthropic API if available."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)

            def generate_with_anthropic(card_texts: list[str], language: str) -> str:
                lang_name = "English" if language == "en" else "Spanish"
                sample = "\n".join(card_texts[:10])
                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=256,
                    messages=[{
                        "role": "user",
                        "content": f"Based on these sample cards from a deck, write a brief 1-2 sentence "
                                   f"description of this deck in {lang_name}. Cards:\n\n{sample}",
                    }],
                )
                return response.content[0].text.strip()

            return generate_with_anthropic
        except ImportError:
            pass

    def stub_generator(card_texts: list[str], language: str) -> str:
        return "A collection of cards for reflection and conversation."

    return stub_generator


def _collect_leaf_nodes(nodes: list[DeckNode]) -> list[DeckNode]:
    """Recursively collect all leaf nodes from the tree."""
    result: list[DeckNode] = []
    for node in nodes:
        if node.is_leaf:
            result.append(node)
        if node.children:
            result.extend(_collect_leaf_nodes(node.children))
    return result


def _get_images(deck_dir: Path) -> list[Path]:
    """Get all image files in a deck directory, sorted by name."""
    images = []
    for f in sorted(deck_dir.iterdir()):
        if f.is_file() and f.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
            images.append(f)
    return images


def process_leaf_deck(
    node: DeckNode,
    ocr_cache: OCRCache,
    translation_cache: TranslationCache,
    ocr_provider,
    translate_provider,
    about_generator,
) -> LeafDeckData:
    """Process a single leaf deck: segment, OCR, translate, classify."""
    deck_dir = DECKS_DIR / node.id
    images = _get_images(deck_dir)
    print(f"  Processing {node.id}: {len(images)} image(s)")

    cards: list[Card] = []
    card_idx = 0

    for img_path in images:
        try:
            bboxes = segment_sheet(img_path, deck_dir)
        except SegmentationError as e:
            print(f"    Warning: {e}")
            # Treat entire image as one card
            with Image.open(img_path) as img:
                w, h = img.size
            bboxes = [BBox(x=0, y=0, w=w, h=h)]

        for bbox in bboxes:
            ocr_result = ocr_card_crop(img_path, bbox, ocr_cache, ocr_provider)
            if not ocr_result.text or ocr_result.text == "[OCR not available]":
                card_idx += 1
                continue

            # Classify color from the card crop
            with Image.open(img_path) as img:
                crop = img.crop((bbox.x, bbox.y, bbox.x + bbox.w, bbox.y + bbox.h))
            color = classify_color(crop)

            cards.append(Card(
                id=f"{node.id}/{card_idx}",
                text_en=ocr_result.text,
                text_es=ocr_result.text,
                color=color,
            ))
            card_idx += 1

    # Detect language and translate
    if cards:
        sample_texts = [c.text_en for c in cards[:5]]
        source_lang = detect_language(sample_texts)
        print(f"    Detected language: {source_lang}")

        translated_cards: list[Card] = []
        for card in cards:
            en, es = ensure_bilingual(card.text_en, source_lang, translation_cache, translate_provider)
            translated_cards.append(Card(
                id=card.id,
                text_en=en,
                text_es=es,
                color=card.color,
                symbol=card.symbol,
            ))
        cards = translated_cards

    # Resolve about text
    card_texts = [c.text_en for c in cards]
    about_en, about_es = resolve_about(
        deck_dir, card_texts, "en", translate_provider, about_generator
    )

    # Collect unique colors and symbols
    colors = sorted(set(c.color for c in cards if c.color))
    symbols = sorted(set(c.symbol for c in cards if c.symbol))

    if not cards:
        # Create a placeholder card if no text was extracted
        cards = [Card(
            id=f"{node.id}/0",
            text_en="(No text extracted from this card)",
            text_es="(No se extrajo texto de esta carta)",
        )]

    return LeafDeckData(
        id=node.id,
        name=node.name,
        cards=cards,
        about_en=about_en,
        about_es=about_es,
        colors=colors if colors else None,
        symbols=symbols if symbols else None,
    )


def main() -> None:
    if not DECKS_DIR.is_dir():
        print(f"Error: {DECKS_DIR} directory not found.")
        print("Place your deck images in ./decks/ and try again.")
        sys.exit(1)

    print("Discovering decks...")
    index = discover_decks(DECKS_DIR)
    leaf_nodes = _collect_leaf_nodes(index.decks)

    if not leaf_nodes:
        print("No decks with images found.")
        sys.exit(1)

    print(f"Found {len(leaf_nodes)} leaf deck(s)")

    # Set up providers and caches
    ocr_cache = OCRCache(CACHE_DIR / "ocr")
    translation_cache = TranslationCache(CACHE_DIR / "translation")
    ocr_provider = _get_ocr_provider()
    translate_provider = _get_translation_provider()
    about_generator = _get_about_generator()

    # Ensure output directories exist
    decks_data_dir = DATA_DIR / "decks"
    decks_data_dir.mkdir(parents=True, exist_ok=True)

    # Process each leaf deck
    for node in leaf_nodes:
        deck_data = process_leaf_deck(
            node, ocr_cache, translation_cache,
            ocr_provider, translate_provider, about_generator,
        )
        data_file = deck_id_to_filename(node.id)
        output_path = DATA_DIR / data_file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(deck_data.model_dump_json(indent=2))
        print(f"  Wrote {output_path}")

    # Write index.json
    index_path = DATA_DIR / "index.json"
    index_path.write_text(index.model_dump_json(indent=2))
    print(f"Wrote {index_path}")

    # Write manifest
    manifest = generate_manifest(DECKS_DIR)
    manifest_path = DATA_DIR / "deck-manifest.json"
    manifest_path.write_text(manifest.model_dump_json(indent=2))
    print(f"Wrote {manifest_path}")

    print("Done!")


if __name__ == "__main__":
    main()
