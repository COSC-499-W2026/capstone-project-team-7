import { afterEach, expect, test, vi } from 'vitest'
import { submitAnswer } from '../../src/frontend/src/api/answer'
import { SessionEndedError } from '../../src/frontend/src/api/sessionEnded'

function fakeBackend(status: number, body: unknown = {}) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

const photo = new File(['fake'], 'room-number.jpg', { type: 'image/jpeg' })

afterEach(() => {
  vi.unstubAllGlobals()
})

test('sends the photo for the current spot and returns the result', async () => {
  const result = { correct: true, attempts: 1, finished: false, next_position: 2 }
  const fetchMock = fakeBackend(200, result)

  expect(await submitAnswer('abc', photo)).toEqual(result)
  expect(fetchMock).toHaveBeenCalledWith('/api/game/abc/answer', {
    method: 'POST',
    headers: { 'Content-Type': 'image/jpeg' },
    body: photo,
  })
})

test('says the session ended so the app can show the login page', async () => {
  fakeBackend(401)

  await expect(submitAnswer('abc', photo)).rejects.toThrow(SessionEndedError)
  await expect(submitAnswer('abc', photo)).rejects.toThrow('Please log in again')
})

test("shows the backend's message for problems like a photo that is too large", async () => {
  fakeBackend(413, { detail: 'Photo is too large' })

  await expect(submitAnswer('abc', photo)).rejects.toThrow('Photo is too large')
  await expect(submitAnswer('abc', photo)).rejects.not.toBeInstanceOf(SessionEndedError)
})

test('shows a general message when the server gives no details', async () => {
  fakeBackend(503, null)

  await expect(submitAnswer('abc', photo)).rejects.toThrow('Could not send your photo')
})
