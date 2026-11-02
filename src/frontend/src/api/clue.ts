// Asks the backend for the current clue of a game: which spot, which building, and where its audio is.

import { SessionEndedError } from './sessionEnded'

export interface Clue {
  position: number
  total_locations: number
  building: string
  audio_url: string
  elapsed_seconds: number
}

export async function getClue(gameId: string): Promise<Clue> {
  const res = await fetch(`/api/game/${gameId}/clue`)

  if (res.status === 401) throw new SessionEndedError()
  if (res.status === 404) throw new Error('Game not found')
  if (res.status === 409) throw new Error('This game is already finished')
  if (!res.ok) throw new Error('Could not load the clue, please try again')

  return res.json() as Promise<Clue>
}
