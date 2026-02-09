"""Tests for data schemas used by the pipeline and consumed by the frontend."""

import json

import pytest
from pydantic import ValidationError

from scripts.schema import (
    Card,
    DeckManifest,
    DeckManifestEntry,
    DeckNode,
    DeckTreeIndex,
    LeafDeckData,
)


class TestCard:
    def test_valid_card(self):
        card = Card(
            id="card-001",
            text_en="What makes you happy?",
            text_es="Que te hace feliz?",
        )
        assert card.id == "card-001"
        assert card.text_en == "What makes you happy?"
        assert card.text_es == "Que te hace feliz?"

    def test_card_with_categories(self):
        card = Card(
            id="card-002",
            text_en="Describe your ideal day",
            text_es="Describe tu dia ideal",
            color="blue",
            symbol="star",
        )
        assert card.color == "blue"
        assert card.symbol == "star"

    def test_card_categories_optional(self):
        card = Card(
            id="card-003",
            text_en="Hello",
            text_es="Hola",
        )
        assert card.color is None
        assert card.symbol is None

    def test_card_missing_required_field(self):
        with pytest.raises(ValidationError):
            Card(id="card-004", text_en="Hello")  # type: ignore[call-arg]

    def test_card_empty_id_rejected(self):
        with pytest.raises(ValidationError):
            Card(id="", text_en="Hello", text_es="Hola")


class TestLeafDeckData:
    def test_valid_leaf_deck(self):
        deck = LeafDeckData(
            id="emotional/connection",
            name="Connection",
            cards=[
                Card(id="c1", text_en="Hi", text_es="Hola"),
                Card(id="c2", text_en="Bye", text_es="Adios"),
            ],
        )
        assert deck.id == "emotional/connection"
        assert len(deck.cards) == 2

    def test_leaf_deck_with_about(self):
        deck = LeafDeckData(
            id="touch",
            name="Touch",
            cards=[Card(id="c1", text_en="Hi", text_es="Hola")],
            about_en="A deck about touch",
            about_es="Un mazo sobre el tacto",
        )
        assert deck.about_en == "A deck about touch"
        assert deck.about_es == "Un mazo sobre el tacto"

    def test_leaf_deck_about_optional(self):
        deck = LeafDeckData(
            id="touch",
            name="Touch",
            cards=[Card(id="c1", text_en="Hi", text_es="Hola")],
        )
        assert deck.about_en is None
        assert deck.about_es is None

    def test_leaf_deck_empty_cards_rejected(self):
        with pytest.raises(ValidationError):
            LeafDeckData(id="empty", name="Empty", cards=[])

    def test_leaf_deck_categories_lists(self):
        deck = LeafDeckData(
            id="test",
            name="Test",
            cards=[
                Card(id="c1", text_en="Hi", text_es="Hola", color="red", symbol="heart"),
            ],
            colors=["red", "blue"],
            symbols=["heart", "star"],
        )
        assert deck.colors == ["red", "blue"]
        assert deck.symbols == ["heart", "star"]

    def test_leaf_deck_serialization_roundtrip(self):
        deck = LeafDeckData(
            id="test",
            name="Test",
            cards=[Card(id="c1", text_en="Hi", text_es="Hola")],
        )
        json_str = deck.model_dump_json()
        parsed = json.loads(json_str)
        restored = LeafDeckData.model_validate(parsed)
        assert restored == deck


class TestDeckNode:
    def test_leaf_node(self):
        node = DeckNode(
            id="touch",
            name="Touch",
            is_leaf=True,
            data_file="decks/touch.json",
        )
        assert node.is_leaf is True
        assert node.data_file == "decks/touch.json"
        assert node.children is None

    def test_branch_node(self):
        node = DeckNode(
            id="emotional",
            name="Emotional",
            is_leaf=False,
            children=[
                DeckNode(
                    id="emotional/connection",
                    name="Connection",
                    is_leaf=True,
                    data_file="decks/emotional--connection.json",
                ),
            ],
        )
        assert node.is_leaf is False
        assert node.children is not None
        assert len(node.children) == 1

    def test_hybrid_node(self):
        """A directory that has both images (is_leaf) and children."""
        node = DeckNode(
            id="emotional",
            name="Emotional",
            is_leaf=True,
            data_file="decks/emotional.json",
            children=[
                DeckNode(
                    id="emotional/connection",
                    name="Connection",
                    is_leaf=True,
                    data_file="decks/emotional--connection.json",
                ),
            ],
        )
        assert node.is_leaf is True
        assert node.data_file is not None
        assert node.children is not None

    def test_leaf_requires_data_file(self):
        with pytest.raises(ValidationError):
            DeckNode(id="bad", name="Bad", is_leaf=True)  # no data_file


class TestDeckTreeIndex:
    def test_valid_index(self):
        index = DeckTreeIndex(
            decks=[
                DeckNode(
                    id="touch",
                    name="Touch",
                    is_leaf=True,
                    data_file="decks/touch.json",
                ),
            ]
        )
        assert len(index.decks) == 1

    def test_empty_index_allowed(self):
        index = DeckTreeIndex(decks=[])
        assert len(index.decks) == 0

    def test_serialization_roundtrip(self):
        index = DeckTreeIndex(
            decks=[
                DeckNode(
                    id="emotional",
                    name="Emotional",
                    is_leaf=False,
                    children=[
                        DeckNode(
                            id="emotional/connection",
                            name="Connection",
                            is_leaf=True,
                            data_file="decks/emotional--connection.json",
                        ),
                    ],
                ),
            ]
        )
        json_str = index.model_dump_json()
        parsed = json.loads(json_str)
        restored = DeckTreeIndex.model_validate(parsed)
        assert restored == index


class TestDeckManifest:
    def test_valid_manifest(self):
        manifest = DeckManifest(
            entries=[
                DeckManifestEntry(
                    deck_id="touch",
                    fingerprint="abc123",
                    data_file="decks/touch.json",
                ),
            ]
        )
        assert len(manifest.entries) == 1

    def test_manifest_entry_requires_all_fields(self):
        with pytest.raises(ValidationError):
            DeckManifestEntry(deck_id="touch", fingerprint="abc123")  # type: ignore[call-arg]

    def test_manifest_serialization(self):
        manifest = DeckManifest(
            entries=[
                DeckManifestEntry(
                    deck_id="touch",
                    fingerprint="abc123",
                    data_file="decks/touch.json",
                ),
            ]
        )
        json_str = manifest.model_dump_json()
        parsed = json.loads(json_str)
        restored = DeckManifest.model_validate(parsed)
        assert restored == manifest
