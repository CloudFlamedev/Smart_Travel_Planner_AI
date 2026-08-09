import { Moon, Sun } from 'lucide-react'

export type Theme = 'light' | 'dark'

interface ThemeToggleProps {
  theme: Theme
  onToggle: () => void
}

export function ThemeToggle({ theme, onToggle }: ThemeToggleProps) {
  const isDark = theme === 'dark'

  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={onToggle}
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
      title={`Switch to ${isDark ? 'light' : 'dark'} mode`}
    >
      <Sun aria-hidden="true" className="theme-icon theme-icon-sun" size={16} />
      <Moon aria-hidden="true" className="theme-icon theme-icon-moon" size={16} />
      <span className="sr-only">Switch theme</span>
    </button>
  )
}
