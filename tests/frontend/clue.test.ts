import { afterEach, expect, test, vi } from 'vitest'
import { getClue } from '../../src/frontend/src/api/clue'
import { SessionEndedError } from '../../src/frontend/src/api/sessionEnded'

// Pretend to be the backend so the tests don't need a real server.
function fakeBackend(status: number, body: unknown = {}) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => {
  vi.unstubAllGlobals()
})

test('gets the current clue and the time since the game started', async () => {
  const clue = { position: 1, total_locations: 5, building: 'LIB', audio_url: '/api/game/abc/clue/audio',
    elapsed_seconds: 90 }
  const fetchMock = fakeBackend(200, clue)

  expect(await getClue('abc')).toEqual(clue)
  expect(fetchMock).toHaveBeenCalledWith('/api/game/abc/clue')
})

test('says the session ended so the app can show the login page', async () => {
  fakeBackend(401)

  await expect(getClue('abc')).rejects.toThrow(SessionEndedError)
  await expect(getClue('abc')).rejects.toThrow('Please log in again')
})

test('says when the game does not exist or is not yours', async () => {
  fakeBackend(404)

  await expect(getClue('abc')).rejects.toThrow('Game not found')
  await expect(getClue('abc')).rejects.not.toBeInstanceOf(SessionEndedError)
})

test('says when the game is already finished', async () => {
  fakeBackend(409)

  await expect(getClue('abc')).rejects.toThrow('This game is already finished')
})

test('shows a general message for server problems', async () => {
  fakeBackend(503)

  await expect(getClue('abc')).rejects.toThrow('Could not load the clue')
})
