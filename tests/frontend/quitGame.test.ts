import { afterEach, expect, test, vi } from 'vitest'
import { quitGame } from '../../src/frontend/src/api/game'
import { SessionEndedError } from '../../src/frontend/src/api/sessionEnded'

afterEach(() => {
  vi.unstubAllGlobals()
})

test('quitting sends a POST to the game\'s quit endpoint', async () => {
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({}) })
  vi.stubGlobal('fetch', fetchMock)

  await quitGame('abc')

  expect(fetchMock).toHaveBeenCalledWith('/api/game/abc/quit', { method: 'POST' })
})

test('quitting says the session ended so the app can show the login page', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 401 }))

  await expect(quitGame('abc')).rejects.toThrow(SessionEndedError)
})

test('quitting a game that already ended explains why', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 409 }))

  await expect(quitGame('abc')).rejects.toThrow('This game has already ended')
})

test('other problems show a friendly message', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 503 }))
  await expect(quitGame('abc')).rejects.toThrow('Could not quit the game, please try again')

  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
  await expect(quitGame('abc')).rejects.toThrow('Could not quit the game, please try again')
})
