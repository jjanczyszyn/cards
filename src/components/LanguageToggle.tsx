import type { Lang } from '../lib/i18n'
import { t } from '../lib/i18n'

interface Props {
  lang: Lang
  onToggle: () => void
}

export function LanguageToggle({ lang, onToggle }: Props) {
  return (
    <button
      onClick={onToggle}
      className="fixed top-4 right-4 px-3 py-1.5 rounded-full bg-gray-100 text-gray-700 text-sm font-medium hover:bg-gray-200 transition-colors"
      aria-label="Toggle language"
    >
      {t(lang).language}
    </button>
  )
}
