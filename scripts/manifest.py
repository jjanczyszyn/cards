"""Manifest fingerprinting and staleness detection."""

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from scripts.discovery import SUPPORTED_IMAGE_EXTENSIONS, deck_id_to_filename, discover_decks
from scripts.schema import DeckManifest, DeckManifestEntry, DeckNode

# Files that contribute to a deck's fingerprint (besides images).
FINGERPRINT_EXTRAS = {"deck.config.json", "about.txt", "about.en.txt", "about.es.txt"}


def compute_deck_fingerprint(deck_dir: Path) -> str:
    """Compute a SHA-256 fingerprint for a leaf deck directory.

    Includes content hashes of all image files, config files, and about files,
    sorted by name for determinism.
    """
    h = hashlib.sha256()

    relevant_files: list[Path] = []
    for f in sorted(deck_dir.iterdir()):
        if not f.is_file():
            continue
        if f.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
            relevant_files.append(f)
        elif f.name in FINGERPRINT_EXTRAS:
            relevant_files.append(f)

    for f in relevant_files:
        h.update(f.name.encode())
        h.update(f.read_bytes())

    return h.hexdigest()


def _collect_leaf_decks(node: DeckNode, decks_dir: Path) -> list[tuple[str, Path]]:
    """Collect all leaf deck IDs and their filesystem paths."""
    results: list[tuple[str, Path]] = []
    if node.is_leaf:
        results.append((node.id, decks_dir / node.id.replace("/", "/")))
    if node.children:
        for child in node.children:
            results.extend(_collect_leaf_decks(child, decks_dir))
    return results


def generate_manifest(decks_dir: Path) -> DeckManifest:
    """Generate a manifest with fingerprints for all leaf decks."""
    index = discover_decks(decks_dir)
    entries: list[DeckManifestEntry] = []

    for deck_node in index.decks:
        for deck_id, deck_path in _collect_leaf_decks(deck_node, decks_dir):
            fp = compute_deck_fingerprint(deck_path)
            entries.append(
                DeckManifestEntry(
                    deck_id=deck_id,
                    fingerprint=fp,
                    data_file=deck_id_to_filename(deck_id),
                )
            )

    return DeckManifest(entries=entries)


@dataclass
class StalenessResult:
    """Result of checking for stale data."""

    new_decks: list[str] = field(default_factory=list)
    changed_decks: list[str] = field(default_factory=list)
    removed_decks: list[str] = field(default_factory=list)
    missing_data_files: list[str] = field(default_factory=list)

    @property
    def is_fresh(self) -> bool:
        return (
            not self.new_decks
            and not self.changed_decks
            and not self.removed_decks
            and not self.missing_data_files
        )


def check_staleness(decks_dir: Path, data_dir: Path) -> StalenessResult:
    """Compare current deck state against committed manifest.

    Args:
        decks_dir: Path to the local decks/ directory.
        data_dir: Path to the committed data directory (public/data/).
    """
    result = StalenessResult()
    current = generate_manifest(decks_dir)

    manifest_path = data_dir / "deck-manifest.json"
    if not manifest_path.exists():
        committed = DeckManifest(entries=[])
    else:
        import json
        committed = DeckManifest.model_validate(json.loads(manifest_path.read_text()))

    committed_map = {e.deck_id: e for e in committed.entries}
    current_map = {e.deck_id: e for e in current.entries}

    for deck_id, entry in current_map.items():
        if deck_id not in committed_map:
            result.new_decks.append(deck_id)
        elif entry.fingerprint != committed_map[deck_id].fingerprint:
            result.changed_decks.append(deck_id)
        else:
            # Check that the data file actually exists
            data_file = data_dir / entry.data_file
            if not data_file.exists():
                result.missing_data_files.append(deck_id)

    for deck_id in committed_map:
        if deck_id not in current_map:
            result.removed_decks.append(deck_id)

    return result
