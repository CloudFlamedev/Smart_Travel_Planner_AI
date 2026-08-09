export interface TripRequest {
  source: string
  destination: string
  duration: number
  travelers: number
  budget: number
  interests: string[]
}

export interface Place {
  name: string
  category: string
  description: string
}

export interface TransportOption {
  mode: string
  estimated_cost: string
  duration: string
  recommendation: string
}

export interface ItineraryDay {
  day: number
  activities: string[]
}

export interface TripPlan extends TripRequest {
  places: Place[]
  transport_options: TransportOption[]
  itinerary: ItineraryDay[]
  travel_tips: string[]
}

