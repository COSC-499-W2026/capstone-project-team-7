// Asks the backend to start a new game for the logged-in student.

import { SessionEndedError } from './sessionEnded'

export interface StartGameResult {
  game_id: string
  language_code: string
  difficulty: string
  current_position: number
  total_locations: number
}

export async function startGame(languageCode = 'fr', difficulty = 'basic'): Promise<StartGameResult> {
  const res = await fetch('/api/game/start', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ language_code: languageCode, difficulty }),
  }).catch(() => { throw new Error('Could not start a game, please try again') })

  if (res.status === 401) throw new SessionEndedError()
  if (res.status === 409) throw new Error('Not enough locations for this language yet')
  if (res.status === 422) throw new Error('Please choose a valid language and difficulty')
  if (!res.ok) throw new Error('Could not start a game, please try again')

  return res.json() as Promise<StartGameResult>
}
