import { afterEach, expect, test, vi } from 'vitest'
import { apiRequest } from '../../src/frontend/src/api/request'
import { SessionEndedError } from '../../src/frontend/src/api/sessionEnded'

const errors = { statuses: { 404: 'Class not found' }, fallback: 'Could not load, please try again' }

function fakeBackend(status: number, body: unknown = {}) {
  const fetchMock = vi.fn().mockResolvedValue({ ok: status >= 200 && status < 300, status, json: async () => body })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => vi.unstubAllGlobals())

test('a successful request returns the response', async () => {
  const fetchMock = fakeBackend(200, { id: 'c1' })
  const options = { method: 'POST' }

  const res = await apiRequest('/api/thing', options, errors)

  expect(await res.json()).toEqual({ id: 'c1' })
  expect(fetchMock).toHaveBeenCalledWith('/api/thing', options)
})

test('an ended session returns to login', async () => {
  fakeBackend(401)
  await expect(apiRequest('/api/thing', undefined, errors)).rejects.toThrow(SessionEndedError)
})

test.each([[404, 'Class not found'], [409, 'Could not load, please try again'], [503, 'Could not load, please try again']])(
  'a failed request (%s) explains itself without logging out', async (status, message) => {
    fakeBackend(status)
    const request = apiRequest('/api/thing', undefined, errors)
    await expect(request).rejects.toThrow(message)
    await expect(request).rejects.not.toBeInstanceOf(SessionEndedError)
  })

test('the backend message is shown only when asked for', async () => {
  fakeBackend(422, { detail: 'Please retake the photo' })
  await expect(apiRequest('/api/thing', undefined, errors)).rejects.toThrow('Could not load')
  await expect(apiRequest('/api/thing', undefined, { ...errors, useDetail: true })).rejects.toThrow('Please retake the photo')
})

test.each([[{ detail: [{ msg: 'field required' }] }], [null]])(
  'a missing or unreadable backend message falls back (%j)', async (body) => {
    fakeBackend(422, body)
    await expect(apiRequest('/api/thing', undefined, { ...errors, useDetail: true })).rejects.toThrow('Could not load')
  })

test('no connection offers a retry', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
  await expect(apiRequest('/api/thing', undefined, errors)).rejects.toThrow('Could not connect, please try again')
  await expect(apiRequest('/api/thing', undefined, { ...errors, offline: 'Could not send your photo.' }))
    .rejects.toThrow('Could not send your photo.')
})
