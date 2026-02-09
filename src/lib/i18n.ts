export type Lang = 'en' | 'es'

const UI_STRINGS = {
  en: {
    title: 'Cards',
    chooseDeck: 'Choose a deck',
    drawCard: 'Draw Card',
    noMoreCards: 'No more cards!',
    cardsRemaining: (n: number) => `${n} card${n !== 1 ? 's' : ''} remaining`,
    filterAll: 'All',
    filterColor: 'By Color',
    filterSymbol: 'By Symbol',
    about: 'About this deck',
    back: 'Back',
    language: 'ES',
  },
  es: {
    title: 'Cartas',
    chooseDeck: 'Elige un mazo',
    drawCard: 'Sacar Carta',
    noMoreCards: 'No hay mas cartas!',
    cardsRemaining: (n: number) => `${n} carta${n !== 1 ? 's' : ''} restante${n !== 1 ? 's' : ''}`,
    filterAll: 'Todas',
    filterColor: 'Por Color',
    filterSymbol: 'Por Simbolo',
    about: 'Sobre este mazo',
    back: 'Volver',
    language: 'EN',
  },
} as const

export function t(lang: Lang) {
  return UI_STRINGS[lang]
}
