import { useState, useEffect } from 'react'
import type { DeckTreeIndex, DeckNode, LeafDeckData } from './types/data'
import type { Lang } from './lib/i18n'
import { t } from './lib/i18n'
import { LanguageToggle } from './components/LanguageToggle'
import { DeckPicker } from './components/DeckPicker'
import { CardDraw } from './components/CardDraw'

function App() {
  const [lang, setLang] = useState<Lang>('en')
  const [index, setIndex] = useState<DeckTreeIndex | null>(null)
  const [path, setPath] = useState<DeckNode[]>([])
  const [selectedDeck, setSelectedDeck] = useState<LeafDeckData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/index.json`)
      .then((r) => {
        if (!r.ok) throw new Error(`Failed to load index: ${r.status}`)
        return r.json()
      })
      .then((data: DeckTreeIndex) => {
        setIndex(data)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  const toggleLang = () => setLang((l) => (l === 'en' ? 'es' : 'en'))

  const handleSelectNode = (node: DeckNode) => {
    if (node.is_leaf && node.data_file) {
      setLoading(true)
      fetch(`${import.meta.env.BASE_URL}data/${node.data_file}`)
        .then((r) => {
          if (!r.ok) throw new Error(`Failed to load deck: ${r.status}`)
          return r.json()
        })
        .then((data: LeafDeckData) => {
          setSelectedDeck(data)
          setLoading(false)
        })
        .catch((err) => {
          setError(err.message)
          setLoading(false)
        })
    } else if (node.children) {
      setPath([...path, node])
    }
  }

  const handleBack = () => {
    if (selectedDeck) {
      setSelectedDeck(null)
    } else {
      setPath(path.slice(0, -1))
    }
  }

  const strings = t(lang)

  return (
    <div className="min-h-screen bg-white flex flex-col items-center pt-12 pb-8">
      <LanguageToggle lang={lang} onToggle={toggleLang} />

      <h1 className="text-3xl font-bold mb-8 bg-gradient-to-r from-red-500 via-yellow-500 via-green-500 via-blue-500 to-purple-500 bg-clip-text text-transparent">
        {strings.title}
      </h1>

      {loading && (
        <p className="text-gray-400 text-sm">Loading...</p>
      )}

      {error && (
        <p className="text-red-500 text-sm">{error}</p>
      )}

      {!loading && !error && !selectedDeck && index && (
        <DeckPicker
          decks={index.decks}
          path={path}
          lang={lang}
          onSelect={handleSelectNode}
          onBack={handleBack}
        />
      )}

      {!loading && !error && selectedDeck && (
        <CardDraw
          deck={selectedDeck}
          lang={lang}
          onBack={handleBack}
        />
      )}
    </div>
  )
}

export default App
