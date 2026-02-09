import { useState, useMemo } from 'react'
import type { Card, LeafDeckData } from '../types/data'
import type { Lang } from '../lib/i18n'
import { t } from '../lib/i18n'
import { createDrawState, drawNext, filterCards, type CardFilter } from '../lib/shuffle'

interface Props {
  deck: LeafDeckData
  lang: Lang
  onBack: () => void
}

export function CardDraw({ deck, lang, onBack }: Props) {
  const strings = t(lang)
  const [filter, setFilter] = useState<CardFilter>({})
  const [showAbout, setShowAbout] = useState(false)

  const seed = useMemo(() => Math.random() * 2 ** 32, [])

  const filtered = useMemo(() => filterCards(deck.cards, filter), [deck.cards, filter])

  const [drawState, setDrawState] = useState(() => createDrawState(filtered, seed))
  const [currentCard, setCurrentCard] = useState<Card | null>(null)

  const handleFilterChange = (newFilter: CardFilter) => {
    setFilter(newFilter)
    const newFiltered = filterCards(deck.cards, newFilter)
    setDrawState(createDrawState(newFiltered, Math.random() * 2 ** 32))
    setCurrentCard(null)
  }

  const handleDraw = () => {
    const card = drawNext(drawState)
    setCurrentCard(card)
    setDrawState({ ...drawState })
  }

  const aboutText = lang === 'en' ? deck.about_en : deck.about_es
  const cardText = currentCard
    ? lang === 'en'
      ? currentCard.text_en
      : currentCard.text_es
    : null

  const hasColors = deck.colors && deck.colors.length > 0
  const hasSymbols = deck.symbols && deck.symbols.length > 0

  return (
    <div className="flex flex-col items-center w-full max-w-md mx-auto px-4">
      <button
        onClick={onBack}
        className="self-start mb-4 text-sm text-gray-500 hover:text-gray-700 transition-colors"
      >
        &larr; {strings.back}
      </button>

      <h2 className="text-xl font-semibold text-gray-800 mb-2">{deck.name}</h2>

      {aboutText && (
        <button
          onClick={() => setShowAbout(!showAbout)}
          className="text-xs text-gray-400 hover:text-gray-600 mb-4"
        >
          {strings.about}
        </button>
      )}

      {showAbout && aboutText && (
        <p className="text-sm text-gray-600 mb-4 px-4 py-3 bg-gray-50 rounded-lg">
          {aboutText}
        </p>
      )}

      {(hasColors || hasSymbols) && (
        <div className="flex gap-2 mb-4 flex-wrap justify-center">
          <button
            onClick={() => handleFilterChange({})}
            className={`px-3 py-1 rounded-full text-xs transition-colors ${
              !filter.color && !filter.symbol
                ? 'bg-gray-800 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {strings.filterAll}
          </button>
          {hasColors &&
            deck.colors!.map((color) => (
              <button
                key={color}
                onClick={() => handleFilterChange({ color })}
                className={`px-3 py-1 rounded-full text-xs transition-colors ${
                  filter.color === color
                    ? 'bg-gray-800 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {color}
              </button>
            ))}
          {hasSymbols &&
            deck.symbols!.map((symbol) => (
              <button
                key={symbol}
                onClick={() => handleFilterChange({ symbol })}
                className={`px-3 py-1 rounded-full text-xs transition-colors ${
                  filter.symbol === symbol
                    ? 'bg-gray-800 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {symbol}
              </button>
            ))}
        </div>
      )}

      <div className="w-full min-h-[200px] flex items-center justify-center mb-6">
        {currentCard ? (
          <div className="w-full p-6 rounded-2xl bg-gradient-to-br from-violet-50 via-white to-rose-50 border border-gray-200 shadow-sm">
            <p className="text-lg text-gray-800 text-center leading-relaxed">
              {cardText}
            </p>
            {(currentCard.color || currentCard.symbol) && (
              <div className="flex gap-2 justify-center mt-4">
                {currentCard.color && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500">
                    {currentCard.color}
                  </span>
                )}
                {currentCard.symbol && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500">
                    {currentCard.symbol}
                  </span>
                )}
              </div>
            )}
          </div>
        ) : (
          <p className="text-gray-400 text-sm">
            {drawState.exhausted ? strings.noMoreCards : ''}
          </p>
        )}
      </div>

      <button
        onClick={handleDraw}
        disabled={drawState.exhausted}
        className="w-full py-3 rounded-xl font-medium text-white bg-gradient-to-r from-violet-500 to-rose-500 hover:from-violet-600 hover:to-rose-600 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-sm"
      >
        {strings.drawCard}
      </button>

      <p className="mt-3 text-xs text-gray-400">
        {strings.cardsRemaining(drawState.remaining)}
      </p>
    </div>
  )
}
