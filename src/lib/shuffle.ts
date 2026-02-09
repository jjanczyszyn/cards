import type { Card } from '../types/data'

/**
 * Simple seeded PRNG (mulberry32).
 * Returns a function that produces numbers in [0, 1).
 */
function mulberry32(seed: number): () => number {
  let s = seed | 0
  return () => {
    s = (s + 0x6d2b79f5) | 0
    let t = Math.imul(s ^ (s >>> 15), 1 | s)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

/**
 * Fisher-Yates shuffle with a seeded PRNG.
 * Does not mutate the input array.
 */
export function seededShuffle<T>(items: readonly T[], seed: number): T[] {
  const arr = [...items]
  const rng = mulberry32(seed)
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1))
    ;[arr[i], arr[j]] = [arr[j], arr[i]]
  }
  return arr
}

export interface DrawState {
  readonly order: readonly Card[]
  index: number
  readonly total: number
  readonly remaining: number
  readonly exhausted: boolean
}

/**
 * Create a draw state from a list of cards and a seed.
 */
export function createDrawState(cards: Card[], seed: number): DrawState {
  const order = seededShuffle(cards, seed)
  return {
    order,
    index: 0,
    total: order.length,
    get remaining() {
      return this.total - this.index
    },
    get exhausted() {
      return this.index >= this.total
    },
  }
}

/**
 * Draw the next card from the state. Returns null if exhausted.
 */
export function drawNext(state: DrawState): Card | null {
  if (state.index >= state.total) {
    return null
  }
  const card = state.order[state.index]
  state.index++
  return card
}

export interface CardFilter {
  color?: string
  symbol?: string
}

/**
 * Filter cards by color and/or symbol.
 */
export function filterCards(cards: Card[], filter?: CardFilter): Card[] {
  if (!filter) return cards
  return cards.filter((card) => {
    if (filter.color && card.color !== filter.color) return false
    if (filter.symbol && card.symbol !== filter.symbol) return false
    return true
  })
}
