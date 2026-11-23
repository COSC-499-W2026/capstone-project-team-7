import { apiRequest } from './request'

export interface Difficulty {
  building: string
  room_number: string
  language_code: string
  difficulty: string
  hunts: number
  listens: number
  attempts: number
  extra_attempts: number
  number_text: string | null
  description_text: string | null
}

export interface Debrief {
  completed_hunts: number
  difficulties: Difficulty[]
}

export async function getDebrief(): Promise<Debrief> {
  const response = await apiRequest('/api/student/debrief', undefined,
    { fallback: 'Could not load your debrief. Please try again.' })
  return response.json() as Promise<Debrief>
}
