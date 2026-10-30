// Asks the backend for the logged-in student's unfinished games, newest first.

import type { StartGameResult } from './game'
import { SessionEndedError } from './sessionEnded'

export interface OngoingGame extends StartGameResult {
  started_at: string
}

export async function getOngoingGames(): Promise<OngoingGame[]> {
  const res = await fetch('/api/game/ongoing')

  if (res.status === 401) throw new SessionEndedError()
  if (!res.ok) throw new Error('Could not load your games, please try again')

  return res.json() as Promise<OngoingGame[]>
}
