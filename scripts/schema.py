"""Data schemas for the card deck pipeline.

These define the structure of all JSON artifacts produced by the pipeline
and consumed by the frontend.
"""

from pydantic import BaseModel, field_validator, model_validator


class Card(BaseModel):
    """A single card with bilingual text and optional categories."""

    id: str
    text_en: str
    text_es: str
    color: str | None = None
    symbol: str | None = None

    @field_validator("id")
    @classmethod
    def id_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Card id must not be empty")
        return v


class LeafDeckData(BaseModel):
    """Full data for a leaf deck, written as an individual JSON file."""

    id: str
    name: str
    cards: list[Card]
    about_en: str | None = None
    about_es: str | None = None
    colors: list[str] | None = None
    symbols: list[str] | None = None

    @field_validator("cards")
    @classmethod
    def cards_not_empty(cls, v: list[Card]) -> list[Card]:
        if len(v) == 0:
            raise ValueError("A deck must contain at least one card")
        return v


class DeckNode(BaseModel):
    """A node in the deck selection tree (index.json)."""

    id: str
    name: str
    is_leaf: bool
    data_file: str | None = None
    children: list["DeckNode"] | None = None

    @model_validator(mode="after")
    def leaf_requires_data_file(self) -> "DeckNode":
        if self.is_leaf and self.data_file is None:
            raise ValueError("Leaf nodes must have a data_file")
        return self


class DeckTreeIndex(BaseModel):
    """Top-level index.json listing the full deck tree."""

    decks: list[DeckNode]


class DeckManifestEntry(BaseModel):
    """One entry in the deck manifest tracking source fingerprints."""

    deck_id: str
    fingerprint: str
    data_file: str


class DeckManifest(BaseModel):
    """Manifest tracking all leaf decks and their source fingerprints."""

    entries: list[DeckManifestEntry]
