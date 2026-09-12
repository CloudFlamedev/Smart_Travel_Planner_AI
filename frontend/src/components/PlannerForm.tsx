import { type FormEvent, type ReactNode, useState } from 'react'
import { ArrowRight, CalendarDays, CircleAlert, IndianRupee, MapPin, UsersRound, WandSparkles } from 'lucide-react'
import type { TripRequest } from '../types'

interface Props {
  initialValues: TripRequest
  loading: boolean
  error: string
  onSubmit: (values: TripRequest) => Promise<void>
}

const fieldClass = 'field-input'

type NumericFieldKey = 'duration' | 'travelers' | 'budget'
const NUMERIC_LIMITS: Record<NumericFieldKey, { min: number; max: number }> = {
  duration: { min: 1, max: 30 },
  travelers: { min: 1, max: 20 },
  budget: { min: 1, max: 10_000_000 },
}

export function PlannerForm({ initialValues, loading, error, onSubmit }: Props) {
  const [values, setValues] = useState({
    ...initialValues,
    duration: String(initialValues.duration),
    travelers: String(initialValues.travelers),
    budget: String(initialValues.budget),
    interestsText: '',
  })
  const [validation, setValidation] = useState('')
  const update = (key: 'source' | 'destination' | 'interestsText', value: string) => setValues((previous) => ({ ...previous, [key]: value }))

  // Keep numeric fields as sanitized strings (not numbers) so the box can be
  // genuinely empty while editing, and so leading zeros never get typed
  // alongside a real digit (e.g. "0" then "5" showing "05").
  const updateNumeric = (key: NumericFieldKey, raw: string) => {
    const digitsOnly = raw.replace(/[^0-9]/g, '')
    const withoutLeadingZeros = digitsOnly.replace(/^0+(?=\d)/, '')
    setValues((previous) => ({ ...previous, [key]: withoutLeadingZeros }))
  }

  // On blur, clamp to the field's valid range so an empty or out-of-range
  // value (e.g. "999" days) never reaches submit as-is.
  const clampNumeric = (key: NumericFieldKey) => () => {
    const { min, max } = NUMERIC_LIMITS[key]
    setValues((previous) => {
      const parsed = Number(previous[key])
      const safe = previous[key] === '' || Number.isNaN(parsed) ? min : Math.min(Math.max(parsed, min), max)
      return { ...previous, [key]: String(safe) }
    })
  }

  async function submit(event: FormEvent) {
    event.preventDefault()
    const duration = Number(values.duration || 0)
    const travelers = Number(values.travelers || 0)
    const budget = Number(values.budget || 0)
    if (!values.source.trim() || !values.destination.trim() || duration < 1 || travelers < 1 || budget < 1) {
      setValidation('Please complete all required trip details.')
      return
    }
    setValidation('')
    await onSubmit({
      source: values.source.trim(),
      destination: values.destination.trim(),
      duration,
      travelers,
      budget,
      interests: values.interestsText.split(',').map((interest) => interest.trim()).filter(Boolean),
    })
  }

  const message = validation || error

  return (
    <form onSubmit={submit} className="planner-card">
      <div className="planner-card-heading">
        <div>
          <p className="section-kicker"><WandSparkles size={14} aria-hidden="true" /> Your next escape</p>
          <h2>Tell us about the trip.</h2>
        </div>
        <p>We’ll turn the essentials into a practical, personalized itinerary.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Field label="From" icon={<MapPin size={16} />}>
          <input className={fieldClass} value={values.source} onChange={(event) => update('source', event.target.value)} placeholder="Bangalore" aria-label="Source city" />
        </Field>
        <Field label="To" icon={<MapPin size={16} />}>
          <input className={fieldClass} value={values.destination} onChange={(event) => update('destination', event.target.value)} placeholder="Delhi" aria-label="Destination city" />
        </Field>
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-3">
        <Field label="Duration" icon={<CalendarDays size={16} />} suffix="days">
          <input className={`${fieldClass} field-input-suffix`} type="number" inputMode="numeric" min="1" max="30" value={values.duration} onChange={(event) => updateNumeric('duration', event.target.value)} onBlur={clampNumeric('duration')} aria-label="Duration in days" />
        </Field>
        <Field label="Travelers" icon={<UsersRound size={16} />}>
          <input className={fieldClass} type="number" inputMode="numeric" min="1" max="20" value={values.travelers} onChange={(event) => updateNumeric('travelers', event.target.value)} onBlur={clampNumeric('travelers')} aria-label="Number of travelers" />
        </Field>
        <Field label="Budget" icon={<IndianRupee size={16} />} suffix="INR">
          <input className={`${fieldClass} field-input-suffix`} type="number" inputMode="numeric" min="1" value={values.budget} onChange={(event) => updateNumeric('budget', event.target.value)} onBlur={clampNumeric('budget')} aria-label="Budget in rupees" />
        </Field>
      </div>

      <div className="mt-4">
        <label className="field-label" htmlFor="interests">Interests <span>(optional)</span></label>
        <input id="interests" className={fieldClass} value={values.interestsText} onChange={(event) => update('interestsText', event.target.value)} placeholder="History, food, culture" />
      </div>

      {message && <p role="alert" className="form-alert"><CircleAlert aria-hidden="true" size={18} />{message}</p>}

      <div className="planner-submit-row">
        <p>Transport costs are approximate estimates, never live prices.</p>
        <button type="submit" disabled={loading} className="generate-button">
          {loading ? <><span className="loader" aria-hidden="true" /> Creating your personalized trip...</> : <>Generate my trip <WandSparkles size={17} aria-hidden="true" /><ArrowRight className="button-arrow" size={17} aria-hidden="true" /></>}
        </button>
      </div>

      {loading && <div className="generation-status" role="status" aria-live="polite"><div className="route-pulse" aria-hidden="true"><span /><span /><span /></div><div><strong>Mapping your best route</strong><p>Finding ideas, practical transport, and a day-by-day rhythm.</p></div></div>}
    </form>
  )
}

function Field({ label, icon, suffix, children }: { label: string; icon: ReactNode; suffix?: string; children: ReactNode }) {
  return (
    <label className="field-shell">
      <span className="field-label">{icon}{label}</span>
      {children}
      {suffix && <span className="field-suffix">{suffix}</span>}
    </label>
  )
}
