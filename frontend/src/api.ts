import axios from 'axios'
import type { TripPlan, TripRequest } from './types'

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL ?? '', timeout: 45000 })

export async function generateTrip(payload: TripRequest): Promise<TripPlan> {
  const response = await api.post<TripPlan>('/api/trips/plan', payload)
  return response.data
}

export function userFacingError(error: unknown): string {
  if (axios.isAxiosError(error) && typeof error.response?.data?.detail === 'string') return error.response.data.detail
  return 'Unable to generate your trip right now. Please try again.'
}

