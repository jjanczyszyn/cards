import type { DeckNode } from '../types/data'
import type { Lang } from '../lib/i18n'
import { t } from '../lib/i18n'

interface Props {
  decks: DeckNode[]
  path: DeckNode[]
  lang: Lang
  onSelect: (node: DeckNode) => void
  onBack: () => void
}

export function DeckPicker({ decks, path, lang, onSelect, onBack }: Props) {
  const strings = t(lang)
  const current = path.length > 0 ? path[path.length - 1] : null
  const items = current?.children ?? decks

  return (
    <div className="flex flex-col items-center w-full max-w-md mx-auto px-4">
      <h2 className="text-xl font-semibold text-gray-800 mb-6">{strings.chooseDeck}</h2>

      {path.length > 0 && (
        <button
          onClick={onBack}
          className="self-start mb-4 text-sm text-gray-500 hover:text-gray-700 transition-colors"
        >
          &larr; {strings.back}
        </button>
      )}

      <div className="w-full space-y-3">
        {items?.map((node) => (
          <button
            key={node.id}
            onClick={() => onSelect(node)}
            className="w-full p-4 rounded-xl bg-gradient-to-r from-purple-50 to-pink-50 border border-gray-200 text-left hover:shadow-md transition-shadow"
          >
            <span className="font-medium text-gray-800">{node.name}</span>
            {!node.is_leaf && node.children && (
              <span className="ml-2 text-xs text-gray-400">{node.children.length} sub-decks</span>
            )}
            {node.is_leaf && (
              <span className="ml-2 text-xs text-gray-400">&rarr;</span>
            )}
          </button>
        ))}
      </div>
    </div>
  )
}
