import { AlertTriangle, BusFront, Clock3, Lightbulb, MapPin, Plane, Route, Sparkles, TrainFront } from 'lucide-react'
import type { ReactNode } from 'react'
import type { TransportOption, TripPlan } from '../types'

const icons: Record<string, ReactNode> = {
  flight: <Plane size={21} />,
  train: <TrainFront size={21} />,
  bus: <BusFront size={21} />,
}

const formatBudget = (value: number) => new Intl.NumberFormat('en-IN', {
  style: 'currency', currency: 'INR', maximumFractionDigits: 0,
}).format(value)

export function TripResults({ plan }: { plan: TripPlan }) {
  return (
    <section id="trip-results" className="results-section scroll-mt-4 px-5 py-16 sm:px-8 lg:py-24">
      <div className="mx-auto max-w-6xl">
        <header className="results-header">
          <div className="results-intro">
            <p className="section-kicker"><Sparkles size={15} aria-hidden="true" /> Your custom plan</p>
            <h2 className="font-display">Hello, <em>{plan.destination}</em>.</h2>
            <p>A considered {plan.duration}-day escape, shaped around how you want to travel.</p>
          </div>
          <div className="snapshot-card" aria-label="Trip snapshot">
            <p>Trip snapshot</p>
            <div className="snapshot-route"><span>{plan.source}</span><Route aria-hidden="true" size={17} /><span>{plan.destination}</span></div>
            <div className="snapshot-details"><span>{plan.travelers} traveler{plan.travelers > 1 ? 's' : ''}</span><span>{plan.duration} days</span><strong>{formatBudget(plan.budget)}</strong></div>
          </div>
        </header>

        {plan.budget_warning && (
          <div className="budget-warning-banner" role="alert">
            <AlertTriangle aria-hidden="true" size={19} />
            <p>{plan.budget_warning}</p>
          </div>
        )}

        <div className="results-feature-grid">
          <section>
            <SectionTitle title="Places to visit" subtitle="A balance of the essential, the local, and the memorable." />
            <div className="places-grid">
              {plan.places.map((place, index) => <article key={place.name} className="place-card result-card" style={{ animationDelay: `${index * 55}ms` }}>
                <div className="place-card-top"><span className="place-number">0{index + 1}</span><span className="category-badge"><MapPin size={12} aria-hidden="true" />{place.category}</span></div>
                <h3>{place.name}</h3><p>{place.description}</p>
              </article>)}
            </div>
          </section>

          <aside className="tips-card result-card">
            <div className="tips-icon"><Lightbulb aria-hidden="true" size={23} /></div>
            <p className="tips-eyebrow"><Sparkles size={13} aria-hidden="true" /> AI travel notes</p>
            <h2>Make it feel effortless.</h2>
            <ul>{plan.travel_tips.map((tip, index) => <li key={tip}><span>{index + 1}</span><p>{tip}</p></li>)}</ul>
          </aside>
        </div>

        <section className="results-group">
          <SectionTitle title="Getting there" subtitle="All prices are estimates and may change before you book." />
          <div className="transport-grid">{plan.transport_options.map((option, index) => <TransportCard key={option.mode} option={option} index={index} />)}</div>
        </section>

        <section className="results-group itinerary-section">
          <SectionTitle title="Your day-by-day rhythm" subtitle="Enough structure to see the highlights, with plenty of room to wander." />
          <div className="itinerary-grid">
            {plan.itinerary.map((item, itemIndex) => <article key={item.day} className="itinerary-card result-card" style={{ animationDelay: `${itemIndex * 70}ms` }}>
              <div className="itinerary-day"><span>Day</span><strong>{String(item.day).padStart(2, '0')}</strong><Clock3 aria-hidden="true" size={19} /></div>
              <ol>{item.activities.map((activity, index) => <li key={activity}><span>{String(index + 1).padStart(2, '0')}</span><p>{activity}</p></li>)}</ol>
            </article>)}
          </div>
        </section>
      </div>
    </section>
  )
}

function SectionTitle({ title, subtitle }: { title: string; subtitle: string }) {
  return <div className="section-title"><h2 className="font-display">{title}</h2><p>{subtitle}</p></div>
}

function TransportCard({ option, index }: { option: TransportOption; index: number }) {
  const icon = icons[option.mode.toLowerCase()] ?? <Route size={21} />
  return (
    <article className={`transport-card transport-card-${option.mode.toLowerCase()} result-card`} style={{ animationDelay: `${index * 65}ms` }}>
      <div className="transport-card-top"><span className="transport-icon">{icon}</span><span className="transport-order">0{index + 1}</span></div>
      <h3>{option.mode}</h3>
      <p className="transport-cost">{option.estimated_cost}</p>
      <p className="transport-duration"><Clock3 size={14} aria-hidden="true" /> Approx. journey: {option.duration}</p>
      <p className="transport-recommendation">{option.recommendation}</p>
    </article>
  )
}
