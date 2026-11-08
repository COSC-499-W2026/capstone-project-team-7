import { afterEach, expect, test, vi } from 'vitest'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { assignHunt } from '../../src/frontend/src/api/assignHunt'
import { SessionEndedError } from '../../src/frontend/src/api/sessionEnded'
import AssignHuntForm from '../../src/frontend/src/components/AssignHuntForm'

afterEach(() => vi.unstubAllGlobals())

test('assigns a hunt to the class and returns it', async () => {
  const hunt = { id: 'h1', class_id: 'c1', language_code: 'fr', difficulty: 'advanced', due_date: '2026-12-01' }
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 201, json: async () => hunt })
  vi.stubGlobal('fetch', fetchMock)
  expect(await assignHunt('c1', 'advanced', '2026-12-01')).toEqual(hunt)
  expect(fetchMock).toHaveBeenCalledWith('/api/teacher/classes/c1/hunts', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ difficulty: 'advanced', due_date: '2026-12-01' }),
  })
})

test('an empty due date is sent as null', async () => {
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 201, json: async () => ({}) })
  vi.stubGlobal('fetch', fetchMock)
  await assignHunt('c1', 'basic', '')
  expect(fetchMock.mock.calls[0][1].body).toBe(JSON.stringify({ difficulty: 'basic', due_date: null }))
})

test('expired sessions request a return to login', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 401 }))
  await expect(assignHunt('c1', 'basic', '')).rejects.toThrow(SessionEndedError)
})

test.each([
  [422, "Due date can't be in the past"], [403, "You can't assign hunts to this class"],
  [404, "You can't assign hunts to this class"], [503, 'Could not assign the hunt, please try again'],
] as const)('assigning a hunt explains failures (%s)', async (status, message) => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status }))
  await expect(assignHunt('c1', 'basic', '')).rejects.toThrow(message)
})

test('network failures explain that the teacher can retry', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
  await expect(assignHunt('c1', 'basic', '')).rejects.toThrow('Could not assign the hunt, please try again')
})

test('form offers three difficulties, an optional due date and an assign button', () => {
  const html = renderToStaticMarkup(createElement(AssignHuntForm, { classId: 'c1', disabled: false, onSessionEnded: vi.fn() }))
  expect(html.match(/<option /g)).toHaveLength(3)
  expect(html).toContain('type="date"')
  expect(html).not.toContain('required')
  expect(html).toContain('<button type="submit">Assign hunt</button>')
})
