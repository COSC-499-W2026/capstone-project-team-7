// Asks the backend for every badge, marking which ones the logged-in student has earned.

import { SessionEndedError } from './sessionEnded'

export interface Badge {
  id: string
  name: string
  language: string | null
  earned: boolean
  earned_at: string | null
}

export async function getBadges(): Promise<Badge[]> {
  const res = await fetch('/api/student/badges')

  if (res.status === 401) throw new SessionEndedError()
  if (!res.ok) throw new Error('Could not load your badges, please try again')

  return res.json() as Promise<Badge[]>
}
