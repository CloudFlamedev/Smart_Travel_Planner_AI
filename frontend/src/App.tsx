import { useEffect, useState } from 'react'
import { Compass, MapPinned, Sparkles } from 'lucide-react'
import { generateTrip, userFacingError } from './api'
import { PlannerForm } from './components/PlannerForm'
import { ThemeToggle, type Theme } from './components/ThemeToggle'
import { TripResults } from './components/TripResults'
import type { TripPlan, TripRequest } from './types'

const initialValues: TripRequest = {
  source: '', destination: '', duration: 4, travelers: 2, budget: 20000, interests: [],
}

function preferredTheme(): Theme {
  try {
    const storedTheme = window.localStorage.getItem('smart-travel-theme')
    if (storedTheme === 'light' || storedTheme === 'dark') return storedTheme
  } catch {
    // Browser privacy settings can disable storage; the system preference still works.
  }
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export default function App() {
  const [plan, setPlan] = useState<TripPlan | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [theme, setTheme] = useState<Theme>(preferredTheme)

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    document.documentElement.style.colorScheme = theme
    try {
      window.localStorage.setItem('smart-travel-theme', theme)
    } catch {
      // The selected theme remains active for the current session.
    }
  }, [theme])

  async function onSubmit(values: TripRequest) {
    setLoading(true)
    setError('')
    try {
      const nextPlan = await generateTrip(values)
      setPlan(nextPlan)
      window.setTimeout(() => document.getElementById('trip-results')?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 60)
    } catch (requestError) {
      setError(userFacingError(requestError))
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="app-shell min-h-screen overflow-hidden">
      <section className="hero-section relative isolate px-5 pb-16 pt-6 sm:px-8 lg:px-12 lg:pb-24">
        <div className="hero-orb hero-orb-one" /><div className="hero-orb hero-orb-two" />
        <nav className="top-nav relative mx-auto flex max-w-6xl items-center justify-between" aria-label="Primary navigation">
          <a href="#planner" className="brand-mark" aria-label="Smart Travel Planner home"><span className="brand-icon"><Compass size={20} /></span><span>smart travel</span></a>
          <div className="nav-actions">
            <span className="ai-nav-badge"><Sparkles size={13} aria-hidden="true" /> AI-powered planning</span>
            <ThemeToggle theme={theme} onToggle={() => setTheme((current) => current === 'dark' ? 'light' : 'dark')} />
          </div>
        </nav>
        <div className="hero-content relative mx-auto max-w-6xl pt-16 text-center sm:pt-24">
          <div className="hero-eyebrow"><Sparkles size={15} aria-hidden="true" /> Thoughtful trips, without the tabs</div>
          <h1 className="hero-title mx-auto max-w-4xl font-display">Plan smarter.<br /><em>Travel better.</em></h1>
          <p className="hero-copy mx-auto mt-7 max-w-xl">Tell us where you’re going, how long you’re staying, and your budget. We’ll shape it into a personal plan worth looking forward to.</p>
        </div>
        <div id="planner" className="planner-wrap relative mx-auto mt-12 max-w-6xl lg:mt-16"><PlannerForm initialValues={initialValues} loading={loading} error={error} onSubmit={onSubmit} /></div>
      </section>
      {plan ? <TripResults plan={plan} /> : <section className="empty-state px-5 py-12 sm:px-8"><div className="empty-state-card mx-auto flex max-w-5xl items-center justify-center gap-4 text-center text-sm"><span className="empty-state-icon"><MapPinned aria-hidden="true" size={20} /></span><p>Your personalized itinerary will appear here once it’s ready.</p></div></section>}
      <footer className="app-footer px-5 py-7 text-center text-sm">Smart Travel Planner <span aria-hidden="true" className="mx-2 opacity-40">•</span> Plan smarter. Travel better.</footer>
    </main>
  )
}
