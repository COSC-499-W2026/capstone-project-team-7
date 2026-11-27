import { afterEach, expect, test, vi } from 'vitest'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { SessionEndedError } from '../../src/frontend/src/api/sessionEnded'
import { addClip, clipAudioUrl, getClips, retireClip } from '../../src/frontend/src/api/teacherClips'
import OwnClips, { clipTitle } from '../../src/frontend/src/components/OwnClips'
import OwnClipsForm from '../../src/frontend/src/components/OwnClipsForm'

afterEach(() => vi.unstubAllGlobals())
const clip = {
  id: 'k1', location_id: 'l1', building: 'COM', room_number: '316', difficulty: 'expert' as const,
  label: 'Café clue', description: null, created_at: '2026-11-26T10:00:00Z',
}
const location = { id: 'l1', building: 'COM', room_number: '316', audio: { basic: true, advanced: false, expert: false } }
const file = new Blob(['mp3'], { type: 'audio/mpeg' })
const operations = [
  () => getClips('c1'),
  () => addClip('c1', 'l1', file, { difficulty: 'basic', label: 'Café clue' }),
  () => retireClip('c1', 'k1'),
]

function fakeBackend(status: number, body: unknown) {
  const fetchMock = vi.fn().mockResolvedValue({ ok: status < 300, status, json: async () => body })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

test('lists the teacher\'s own clips for the class', async () => {
  const fetchMock = fakeBackend(200, [clip])
  expect(await getClips('c1')).toEqual([clip])
  expect(fetchMock).toHaveBeenCalledWith('/api/teacher/classes/c1/clips', undefined)
})

test('adds a clip with the file as the body and trimmed details in the query', async () => {
  const fetchMock = fakeBackend(201, clip)
  expect(await addClip('c1', 'l1', file, { difficulty: 'expert', label: '  Café clue ', description: ' Near the café ' })).toEqual(clip)
  expect(fetchMock).toHaveBeenCalledWith(
    '/api/teacher/classes/c1/locations/l1/clips?difficulty=expert&label=Caf%C3%A9+clue&description=Near+the+caf%C3%A9',
    { method: 'POST', headers: { 'Content-Type': 'audio/mpeg' }, body: file },
  )
})

test('a blank description is left out', async () => {
  const fetchMock = fakeBackend(201, clip)
  await addClip('c1', 'l1', file, { difficulty: 'basic', label: 'Café clue', description: '   ' })
  expect(fetchMock.mock.calls[0][0]).toBe('/api/teacher/classes/c1/locations/l1/clips?difficulty=basic&label=Caf%C3%A9+clue')
})

test('retires a clip and builds its play link', async () => {
  const fetchMock = fakeBackend(204, null)
  await retireClip('c1', 'k1')
  expect(fetchMock).toHaveBeenCalledWith('/api/teacher/classes/c1/clips/k1', { method: 'DELETE' })
  expect(clipAudioUrl('c1', 'k1')).toBe('/api/teacher/classes/c1/clips/k1/audio')
})

test('expired sessions return to login', async () => {
  fakeBackend(401, {})
  for (const operation of operations) await expect(operation()).rejects.toThrow(SessionEndedError)
})

test.each([
  [403, {}, 'Teacher access required'], [404, {}, 'Class, location or clip not found'],
  [413, {}, 'The audio file must be 5 MB or smaller'],
  [422, { detail: 'Please upload an MP3 file' }, 'Please upload an MP3 file'],
  [422, { detail: [{ loc: ['query', 'label'] }] }, 'Check the label (up to 60 characters) and description (up to 300)'],
  [503, {}, 'Could not load or save your clips, please try again'],
] as const)('explains failures (%s)', async (status, body, message) => {
  fakeBackend(status, body)
  for (const operation of operations) await expect(operation()).rejects.toThrow(message)
})

test('network failures offer a friendly retry message', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
  for (const operation of operations) await expect(operation()).rejects.toThrow('Could not connect, please try again')
})

test('a clip is titled by room, level and label', () => {
  expect(clipTitle(clip)).toBe('COM 316 · Expert · Café clue')
})

test('the section starts loading and says clips are private', () => {
  const html = renderToStaticMarkup(createElement(OwnClips, { classId: 'c1', disabled: false, onSessionEnded: vi.fn() }))
  expect(html).toContain('<h2>My clips</h2>')
  expect(html).toContain('Loading your clips...')
  expect(html).toContain('private to you and only play in hunts where you choose them')
})

test('the form needs a label and a file before it can add a clip', () => {
  const html = renderToStaticMarkup(createElement(OwnClipsForm, {
    classId: 'c1', locations: [location], disabled: false, onAdded: vi.fn(), onSessionEnded: vi.fn(),
  }))
  expect(html).toContain('<option value="l1" selected="">COM 316</option>')
  expect(html).toContain('<option value="basic" selected="">Basic</option><option value="advanced">Advanced</option><option value="expert">Expert</option>')
  expect(html).toContain('maxLength="60"')
  expect(html).toContain('maxLength="300"')
  expect(html).toContain('accept="audio/mpeg,.mp3"')
  expect(html).toContain('<button type="submit" disabled="">Add clip</button>')
})

test('without locations the form is disabled', () => {
  const html = renderToStaticMarkup(createElement(OwnClipsForm, {
    classId: 'c1', locations: [], disabled: false, onAdded: vi.fn(), onSessionEnded: vi.fn(),
  }))
  expect(html).toContain('<select id="own-clip-location" disabled="">')
  expect(html).toContain('<input id="own-clip-label" maxLength="60" required="" disabled="" value=""/>')
})
