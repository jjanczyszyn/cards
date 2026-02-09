"""Check committed data artifacts for consistency and staleness."""

import sys
from pathlib import Path

from scripts.manifest import check_staleness


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    decks_dir = project_root / "decks"
    data_dir = project_root / "public" / "data"

    if not decks_dir.is_dir():
        print("No local decks/ directory found. Skipping staleness check.")
        print("(This is expected in CI where source images are not available.)")
        return

    result = check_staleness(decks_dir, data_dir)

    if result.is_fresh:
        print("All deck data is up to date.")
        return

    messages: list[str] = []
    if result.new_decks:
        messages.append(f"New decks need processing: {', '.join(result.new_decks)}")
    if result.changed_decks:
        messages.append(f"Changed decks need reprocessing: {', '.join(result.changed_decks)}")
    if result.removed_decks:
        messages.append(f"Removed decks still in manifest: {', '.join(result.removed_decks)}")
    if result.missing_data_files:
        messages.append(f"Missing data files for: {', '.join(result.missing_data_files)}")

    for msg in messages:
        print(f"STALE: {msg}")

    print("\nRun 'npm run data:build' to regenerate artifacts.")
    sys.exit(1)


if __name__ == "__main__":
    main()
