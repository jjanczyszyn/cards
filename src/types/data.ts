/** A single card with bilingual text and optional categories. */
export interface Card {
  id: string
  text_en: string
  text_es: string
  color?: string | null
  symbol?: string | null
}

/** Full data for a leaf deck JSON file. */
export interface LeafDeckData {
  id: string
  name: string
  cards: Card[]
  about_en?: string | null
  about_es?: string | null
  colors?: string[] | null
  symbols?: string[] | null
}

/** A node in the deck selection tree. */
export interface DeckNode {
  id: string
  name: string
  is_leaf: boolean
  data_file?: string | null
  children?: DeckNode[] | null
}

/** Top-level index.json structure. */
export interface DeckTreeIndex {
  decks: DeckNode[]
}

/** One entry in the deck manifest. */
export interface DeckManifestEntry {
  deck_id: string
  fingerprint: string
  data_file: string
}

/** Manifest tracking all leaf decks and their source fingerprints. */
export interface DeckManifest {
  entries: DeckManifestEntry[]
}
