import { afterEach, expect, test, vi } from 'vitest'
import { startGame } from '../../src/frontend/src/api/game'
import { logout } from '../../src/frontend/src/api/logout'

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

test('start game calls the start endpoint and returns the game', async () => {
  const game = { game_id: 'abc', language_code: 'fr', difficulty: 'basic', current_position: 1, total_locations: 5 }
  const fetchMock = fakeBackend(201, game)

  expect(await startGame()).toEqual(game)
  expect(fetchMock).toHaveBeenCalledWith('/api/game/start', { method: 'POST' })
})

test('start game explains when there are not enough locations', async () => {
  fakeBackend(409)

  await expect(startGame()).rejects.toThrow('Not enough locations for this language yet')
})

test('start game asks to log in again when the session ended', async () => {
  fakeBackend(401)

  await expect(startGame()).rejects.toThrow('Please log in again')
})

test('start game shows a general message for server problems', async () => {
  fakeBackend(503)

  await expect(startGame()).rejects.toThrow('Could not start a game')
})

test('logout calls the logout endpoint', async () => {
  const fetchMock = fakeBackend(200)

  await logout()

  expect(fetchMock).toHaveBeenCalledWith('/api/auth/logout', { method: 'POST' })
})

test('logout still works if the session had already ended', async () => {
  fakeBackend(401)

  await expect(logout()).resolves.toBeUndefined()
})

test('logout shows a message for server problems', async () => {
  fakeBackend(503)

  await expect(logout()).rejects.toThrow('Could not log out')
})
