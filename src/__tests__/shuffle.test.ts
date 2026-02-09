import { describe, it, expect } from 'vitest'
import { seededShuffle, createDrawState, drawNext, filterCards } from '../lib/shuffle'
import type { Card } from '../types/data'

const makeCards = (n: number): Card[] =>
  Array.from({ length: n }, (_, i) => ({
    id: `card-${i}`,
    text_en: `EN ${i}`,
    text_es: `ES ${i}`,
  }))

describe('seededShuffle', () => {
  it('returns all items', () => {
    const cards = makeCards(10)
    const shuffled = seededShuffle(cards, 42)
    expect(shuffled).toHaveLength(10)
    expect(new Set(shuffled.map((c) => c.id)).size).toBe(10)
  })

  it('same seed produces same order', () => {
    const cards = makeCards(20)
    const a = seededShuffle(cards, 12345)
    const b = seededShuffle(cards, 12345)
    expect(a.map((c) => c.id)).toEqual(b.map((c) => c.id))
  })

  it('different seeds produce different orders', () => {
    const cards = makeCards(20)
    const a = seededShuffle(cards, 1)
    const b = seededShuffle(cards, 2)
    const aIds = a.map((c) => c.id)
    const bIds = b.map((c) => c.id)
    // Very unlikely to be the same with 20 items
    expect(aIds).not.toEqual(bIds)
  })

  it('does not mutate the original array', () => {
    const cards = makeCards(5)
    const original = [...cards]
    seededShuffle(cards, 99)
    expect(cards.map((c) => c.id)).toEqual(original.map((c) => c.id))
  })

  it('handles empty array', () => {
    expect(seededShuffle([], 42)).toEqual([])
  })

  it('handles single element', () => {
    const cards = makeCards(1)
    const shuffled = seededShuffle(cards, 42)
    expect(shuffled).toHaveLength(1)
    expect(shuffled[0].id).toBe('card-0')
  })
})

describe('createDrawState / drawNext', () => {
  it('draws cards in shuffled order without repeats', () => {
    const cards = makeCards(5)
    const state = createDrawState(cards, 42)
    const drawn: string[] = []

    for (let i = 0; i < 5; i++) {
      const result = drawNext(state)
      expect(result).not.toBeNull()
      drawn.push(result!.id)
    }

    // No duplicates
    expect(new Set(drawn).size).toBe(5)
  })

  it('returns null after exhausting all cards', () => {
    const cards = makeCards(3)
    const state = createDrawState(cards, 42)

    drawNext(state)
    drawNext(state)
    drawNext(state)
    const result = drawNext(state)
    expect(result).toBeNull()
  })

  it('reports correct remaining count', () => {
    const cards = makeCards(5)
    const state = createDrawState(cards, 42)
    expect(state.remaining).toBe(5)

    drawNext(state)
    expect(state.remaining).toBe(4)

    drawNext(state)
    expect(state.remaining).toBe(3)
  })

  it('exhausted property works', () => {
    const cards = makeCards(2)
    const state = createDrawState(cards, 42)
    expect(state.exhausted).toBe(false)

    drawNext(state)
    drawNext(state)
    expect(state.exhausted).toBe(true)
  })
})

describe('filterCards', () => {
  it('returns all cards with no filter', () => {
    const cards = makeCards(5)
    expect(filterCards(cards)).toHaveLength(5)
  })

  it('filters by color', () => {
    const cards: Card[] = [
      { id: '1', text_en: 'A', text_es: 'A', color: 'red' },
      { id: '2', text_en: 'B', text_es: 'B', color: 'blue' },
      { id: '3', text_en: 'C', text_es: 'C', color: 'red' },
    ]
    const filtered = filterCards(cards, { color: 'red' })
    expect(filtered).toHaveLength(2)
    expect(filtered.every((c) => c.color === 'red')).toBe(true)
  })

  it('filters by symbol', () => {
    const cards: Card[] = [
      { id: '1', text_en: 'A', text_es: 'A', symbol: 'heart' },
      { id: '2', text_en: 'B', text_es: 'B', symbol: 'star' },
      { id: '3', text_en: 'C', text_es: 'C', symbol: 'heart' },
    ]
    const filtered = filterCards(cards, { symbol: 'heart' })
    expect(filtered).toHaveLength(2)
  })

  it('filter reduces candidate set', () => {
    const cards: Card[] = [
      { id: '1', text_en: 'A', text_es: 'A', color: 'red' },
      { id: '2', text_en: 'B', text_es: 'B', color: 'blue' },
      { id: '3', text_en: 'C', text_es: 'C' },
    ]
    const all = filterCards(cards)
    const red = filterCards(cards, { color: 'red' })
    expect(red.length).toBeLessThan(all.length)
  })
})
