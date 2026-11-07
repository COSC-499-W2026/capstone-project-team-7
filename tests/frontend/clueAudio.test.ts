import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { afterEach, expect, test, vi } from 'vitest'
import ClueAudio from '../../src/frontend/src/components/ClueAudio'
import { getClueAudio } from '../../src/frontend/src/api/clueAudio'
import { SessionEndedError } from '../../src/frontend/src/api/sessionEnded'

afterEach(() => vi.unstubAllGlobals())

function render(remaining: number | null) {
  return renderToStaticMarkup(createElement(ClueAudio, { url: '/audio', remaining, onSessionEnded: vi.fn() }))
}

test('shows unlimited Basic plays and enables playback', () => {
  expect(render(null)).toContain('Unlimited audio plays')
  expect(render(null)).not.toContain('disabled')
})

test.each([5, 3, 1])('shows %s plays remaining and enables playback', (remaining) => {
  expect(render(remaining)).toContain(`${remaining} audio plays remaining`)
  expect(render(remaining)).not.toContain('disabled')
})

test('disables exhausted playback without a native player that can replay cached audio', () => {
  expect(render(0)).toContain('disabled')
  expect(render(0)).toContain('No audio plays remaining')
  expect(render(0)).not.toContain('<audio')
})

test.each([['4', 4], ['0', 0], ['unlimited', null]])('uses the server allowance %s', async (header, remaining) => {
  const audio = new Blob(['audio'])
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200,
    headers: new Headers({ 'X-Audio-Plays-Remaining': header }), blob: async () => audio })
  vi.stubGlobal('fetch', fetchMock)
  expect(await getClueAudio('/audio?position=1')).toEqual({ audio, remaining })
  expect(fetchMock).toHaveBeenCalledExactlyOnceWith('/audio?position=1', { cache: 'no-store' })
})

test('handles an expired session', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ status: 401 }))
  await expect(getClueAudio('/audio')).rejects.toThrow(SessionEndedError)
})

test.each([[409, 'No audio plays remaining for this clue'], [404, 'Audio not found for this clue'],
  [503, 'Could not load audio, please try again']])('handles audio error %s', async (status, message) => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ status, ok: false, json: async () => ({ detail: message }) }))
  await expect(getClueAudio('/audio')).rejects.toThrow(message)
})
