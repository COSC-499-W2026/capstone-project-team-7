// Asks the backend for the current clue of a game: which spot, which building, and where its audio is.

import { SessionEndedError } from './sessionEnded'
import { apiRequest } from './request'

export interface Clue {
  position: number
  clue_id: string
  total_locations: number
  building: string | null
  audio_url: string
  elapsed_seconds: number
  clue_elapsed_seconds: number
  revision?: number
}

export async function skipClue(gameId: string, clue: Clue): Promise<Clue> {
  const res = await fetch(`/api/game/${encodeURIComponent(gameId)}/skip?position=${clue.position}&revision=${clue.revision ?? 0}`,
    { method: 'POST' })
  if (res.status === 401) throw new SessionEndedError()
  if (res.status === 409) throw new Error((await res.json()).detail)
  if (!res.ok) throw new Error('Could not skip the location, please try again')
  return res.json() as Promise<Clue>
}

export async function recordCluePlay(gameId: string, clue: Clue): Promise<void> {
  const query = new URLSearchParams({ position: String(clue.position), clue_id: clue.clue_id })
  await apiRequest(`/api/game/${encodeURIComponent(gameId)}/listen?${query}`, {
    method: 'POST',
    keepalive: true,
  }, { fallback: 'Could not record clue playback' })
}

export async function getClue(gameId: string): Promise<Clue> {
  const res = await fetch(`/api/game/${gameId}/clue`)

  if (res.status === 401) throw new SessionEndedError()
  if (res.status === 404) throw new Error('Game not found')
  if (res.status === 409) throw new Error('This game is already finished')
  if (!res.ok) throw new Error('Could not load the clue, please try again')

  return res.json() as Promise<Clue>
}
