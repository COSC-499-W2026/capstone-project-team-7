// Asks the backend for the logged-in student's unfinished games, newest first.

import type { StartGameResult } from './game'
import { apiRequest } from './request'

export interface OngoingGame extends StartGameResult {
  started_at: string
}

export async function getOngoingGames(): Promise<OngoingGame[]> {
  const res = await apiRequest('/api/game/ongoing', undefined, { fallback: 'Could not load your games, please try again' })
  return res.json() as Promise<OngoingGame[]>
}
