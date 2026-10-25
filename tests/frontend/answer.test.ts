import { afterEach, expect, test, vi } from 'vitest'
import { submitAnswer, type AnswerResult } from '../../src/frontend/src/api/answer'

const photo = new File(['photo'], 'room.jpg', { type: 'image/jpeg' })
const correct: AnswerResult = { correct: true, attempts: 1, finished: false, next_position: 2,
  points_awarded: 10, total_points: 20, message: 'Correct room!' }
function backend(status: number, body: unknown) {
  const fetchMock = vi.fn().mockResolvedValue({ ok: status === 200, status, json: async () => body })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}
afterEach(() => vi.unstubAllGlobals())

test('sends the actual photo with session cookies and returns server-awarded points', async () => {
  const fetchMock = backend(200, correct)
  expect(await submitAnswer('abc', photo)).toEqual(correct)
  expect(fetchMock).toHaveBeenCalledWith('/api/game/abc/answer', {
    method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'image/jpeg' }, body: photo,
  })
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
})
