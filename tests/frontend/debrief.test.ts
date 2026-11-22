import { afterEach, expect, test, vi } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'
import { createElement } from 'react'
import { getDebrief, type Debrief } from '../../src/frontend/src/api/debrief'
import { SessionEndedError } from '../../src/frontend/src/api/sessionEnded'
import DebriefView from '../../src/frontend/src/components/DebriefView'

const debrief: Debrief = { completed_hunts: 1, difficulties: [{ building: 'EME', room_number: '101',
  language_code: 'fr', difficulty: 'basic', hunts: 1, listens: 3, attempts: 2, extra_attempts: 1,
  number_text: 'cent un', description_text: 'près de la porte' }] }

afterEach(() => vi.unstubAllGlobals())

test('fetches the student debrief', async () => {
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => debrief })
  vi.stubGlobal('fetch', fetchMock)
  expect(await getDebrief()).toEqual(debrief)
  expect(fetchMock).toHaveBeenCalledWith('/api/student/debrief', undefined)
})

test('handles an expired session and server errors', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 401 }))
  await expect(getDebrief()).rejects.toBeInstanceOf(SessionEndedError)
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 503 }))
  await expect(getDebrief()).rejects.toThrow('Could not load your debrief')
})

test('shows difficult clues and vocabulary in the target language', () => {
  const html = renderToStaticMarkup(createElement(DebriefView, { debrief }))
  expect(html).toContain('Completed hunts: 1')
  expect(html).toContain('EME 101')
  expect(html).toContain('French')
  expect(html).toContain('cent un')
  expect(html).toContain('près de la porte')
  expect(html).toContain('Clue listens: 3')
})

test('asks students without completed hunts to complete one first', () => {
  const html = renderToStaticMarkup(createElement(DebriefView, { debrief: { completed_hunts: 0, difficulties: [] } }))
  expect(html).toContain('Complete a hunt first')
  expect(html).not.toContain('Areas to review')
})

test('explains when no difficulty or vocabulary was recorded', () => {
  expect(renderToStaticMarkup(createElement(DebriefView, { debrief: { completed_hunts: 1, difficulties: [] } })))
    .toContain('No particular difficulties')
  const missing = { ...debrief, difficulties: [{ ...debrief.difficulties[0], number_text: null, description_text: null }] }
  expect(renderToStaticMarkup(createElement(DebriefView, { debrief: missing }))).toContain('Vocabulary is unavailable')
})
