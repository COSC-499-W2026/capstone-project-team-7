import { afterEach, expect, test, vi } from 'vitest'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { SessionEndedError } from '../../src/frontend/src/api/sessionEnded'
import { getClassLocations, uploadClueAudio } from '../../src/frontend/src/api/teacherLocations'
import ClueAudioForm, { locationLabel } from '../../src/frontend/src/components/ClueAudioForm'

afterEach(() => vi.unstubAllGlobals())
const location = { id: 'l1', building: 'COM', room_number: '316', has_audio: true }
const clip = new Blob(['mp3'], { type: 'audio/mpeg' })
const operations = [() => getClassLocations('c1'), () => uploadClueAudio('c1', 'l1', clip)]

function fakeBackend(status: number, body: unknown) {
  const fetchMock = vi.fn().mockResolvedValue({ ok: status < 300, status, json: async () => body })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

test('lists the class locations with their audio status', async () => {
  const fetchMock = fakeBackend(200, [location])
  expect(await getClassLocations('c1')).toEqual([location])
  expect(fetchMock).toHaveBeenCalledWith('/api/teacher/classes/c1/locations', undefined)
})

test('uploads the file as the raw body and returns the saved location', async () => {
  const fetchMock = fakeBackend(200, location)
  expect(await uploadClueAudio('c1', 'l1', clip)).toEqual(location)
  expect(fetchMock).toHaveBeenCalledWith('/api/teacher/classes/c1/locations/l1/audio', {
    method: 'PUT', headers: { 'Content-Type': 'audio/mpeg' }, body: clip,
  })
})

test('expired sessions return to login', async () => {
  fakeBackend(401, {})
  for (const operation of operations) await expect(operation()).rejects.toThrow(SessionEndedError)
})

test.each([
  [403, 'Teacher access required'], [404, 'Class or location not found'],
  [413, 'The audio file must be 5 MB or smaller'], [422, 'Please upload an MP3 file'],
  [503, 'Could not load or save clue audio, please try again'],
] as const)('explains failures (%s)', async (status, message) => {
  fakeBackend(status, {})
  for (const operation of operations) await expect(operation()).rejects.toThrow(message)
})

test('network failures offer a friendly retry message', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
  for (const operation of operations) await expect(operation()).rejects.toThrow('Could not connect, please try again')
})

test('a location is labelled by building and room', () => {
  expect(locationLabel(location)).toBe('COM 316')
})

test('the form starts loading with uploads disabled and says clips are shared', () => {
  const html = renderToStaticMarkup(createElement(ClueAudioForm, { classId: 'c1', disabled: false, onSessionEnded: vi.fn() }))
  expect(html).toContain('Loading locations...')
  expect(html).toContain('accept="audio/mpeg,.mp3"')
  expect(html).toContain('<button type="submit" disabled="">Upload audio</button>')
  expect(html).toContain('changes it for every class that uses this location')
})
