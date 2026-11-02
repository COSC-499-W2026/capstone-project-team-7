import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import { submitAnswer, type AnswerResult } from '../../src/frontend/src/api/answer'
import { SessionEndedError } from '../../src/frontend/src/api/sessionEnded'

const photo = new File(['photo'], 'room.jpg', { type: 'image/jpeg' })
const correct: AnswerResult = { correct: true, attempts: 1, finished: false, next_position: 2,
  points_awarded: 10, total_points: 20, message: 'Correct room!' }
function backend(status: number, body: unknown) {
  const fetchMock = vi.fn().mockResolvedValue({ ok: status === 200, status, json: async () => body })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}
const position = { coords: { latitude: 49.94, longitude: -119.4, accuracy: 10 }, timestamp: Date.now() }
let getCurrentPosition = vi.fn()
beforeEach(() => {
  getCurrentPosition = vi.fn((success) => success(position))
  vi.stubGlobal('navigator', { geolocation: { getCurrentPosition } })
})
afterEach(() => vi.unstubAllGlobals())

test('sends the actual photo with session cookies and returns server-awarded points', async () => {
  const fetchMock = backend(200, correct)
  expect(await submitAnswer('abc', photo)).toEqual(correct)
  expect(fetchMock).toHaveBeenCalledWith(expect.stringMatching(/^\/api\/game\/abc\/answer\?/), {
    method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'image/jpeg' }, body: photo,
  })
  const url = new URL(fetchMock.mock.calls[0][0], 'https://testserver')
  expect(Object.fromEntries(url.searchParams)).toEqual({ latitude: '49.94', longitude: '-119.4',
    accuracy: '10', captured_at: new Date(position.timestamp).toISOString() })
  expect(getCurrentPosition.mock.calls[0][2]).toEqual({ enableHighAccuracy: true, maximumAge: 0, timeout: 10000 })
})

test('an incorrect or unreadable photo stays incorrect and awards no points', async () => {
  backend(200, { ...correct, correct: false, points_awarded: 0, next_position: null })
  expect(await submitAnswer('abc', photo)).toMatchObject({ correct: false, points_awarded: 0 })
})

test.each([[401, {}, 'Please log in again'], [413, { detail: 'Photo is too large' }, 'Photo is too large'],
  [422, { detail: 'Please retake the photo' }, 'Please retake'],
  [503, { detail: 'Recognition unavailable' }, 'Recognition unavailable'], [500, null, 'Could not verify']])(
  'handles HTTP %s without reporting success', async (status, body, message) => {
    backend(status as number, body)
    await expect(submitAnswer('abc', photo)).rejects.toThrow(message as string)
  })

test('says the session ended so the app can show the login page', async () => {
  backend(401, {})
  await expect(submitAnswer('abc', photo)).rejects.toThrow(SessionEndedError)
})

test('other photo errors do not log the student out', async () => {
  backend(413, { detail: 'Photo is too large' })
  await expect(submitAnswer('abc', photo)).rejects.not.toBeInstanceOf(SessionEndedError)
})

test('a network failure allows a retry instead of showing success', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
  await expect(submitAnswer('abc', photo)).rejects.toThrow('Please try again')
})

test.each([{}, { ...correct, points_awarded: undefined }, { ...correct, correct: false }])(
  'rejects incomplete or contradictory verification responses', async (body) => {
    backend(200, body)
    await expect(submitAnswer('abc', photo)).rejects.toThrow('verification is unavailable')
  })

test('an oversized photo is rejected before upload', async () => {
  const fetchMock = backend(200, correct)
  await expect(submitAnswer('abc', new File([new Uint8Array(5 * 1024 * 1024 + 1)], 'large.jpg'))).rejects.toThrow('too large')
  expect(fetchMock).not.toHaveBeenCalled()
  expect(getCurrentPosition).not.toHaveBeenCalled()
})


test.each([[1, 'allow location access'], [2, 'Could not find'], [3, 'timed out']])(
  'location failure %s blocks upload and allows a retry', async (code, message) => {
    const fetchMock = backend(200, correct)
    getCurrentPosition.mockImplementationOnce((_success, failure) => failure({ code }))
    await expect(submitAnswer('abc', photo)).rejects.toThrow(message as string)
    expect(fetchMock).not.toHaveBeenCalled()
    await expect(submitAnswer('abc', photo)).resolves.toEqual(correct)
    expect(getCurrentPosition).toHaveBeenCalledTimes(2)
  })

test('unsupported location blocks upload', async () => {
  vi.stubGlobal('navigator', {})
  const fetchMock = backend(200, correct)
  await expect(submitAnswer('abc', photo)).rejects.toThrow('Location is unavailable')
  expect(fetchMock).not.toHaveBeenCalled()
})

test('waits for the location before uploading the photo', async () => {
  let resolve: (position: unknown) => void = () => {}
  getCurrentPosition.mockImplementationOnce((success) => { resolve = success })
  const fetchMock = backend(200, correct)
  const pending = submitAnswer('abc', photo)
  expect(fetchMock).not.toHaveBeenCalled()
  resolve(position)
  await expect(pending).resolves.toEqual(correct)
})

test('each submission sends the latest reading', async () => {
  const fetchMock = backend(200, correct)
  await submitAnswer('abc', photo)
  const newer = { coords: { ...position.coords, latitude: 49.95 }, timestamp: position.timestamp + 1000 }
  getCurrentPosition.mockImplementationOnce((success) => success(newer))
  await submitAnswer('abc', photo)
  const url = new URL(fetchMock.mock.calls[1][0], 'https://testserver')
  expect(url.searchParams.get('latitude')).toBe('49.95')
  expect(url.searchParams.get('captured_at')).toBe(new Date(newer.timestamp).toISOString())
})

test('server GPS rejection is shown without logging out', async () => {
  backend(422, { detail: 'You are too far from this spot. Move closer and try again.' })
  await expect(submitAnswer('abc', photo)).rejects.toThrow('Move closer')
  await expect(submitAnswer('abc', photo)).rejects.not.toBeInstanceOf(SessionEndedError)
})
