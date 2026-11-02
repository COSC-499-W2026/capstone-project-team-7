import { afterEach, expect, test, vi } from 'vitest'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { createClass } from '../../src/frontend/src/api/teacher'
import { SessionEndedError } from '../../src/frontend/src/api/sessionEnded'
import CreateClassForm from '../../src/frontend/src/components/CreateClassForm'

afterEach(() => vi.unstubAllGlobals())

test('creates a class with a trimmed name and returns its join code', async () => {
  const classroom = { id: 'c1', name: 'German 101', language_code: 'de', class_code: 'ABC123' }
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 201, json: async () => classroom })
  vi.stubGlobal('fetch', fetchMock)
  expect(await createClass('  German 101  ', 'de')).toEqual(classroom)
  expect(fetchMock).toHaveBeenCalledWith('/api/teacher/classes', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: 'German 101', language_code: 'de' }),
  })
})

test('expired sessions request a return to login', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 401 }))
  await expect(createClass('French 101', 'fr')).rejects.toThrow(SessionEndedError)
})

test.each([
  [403, 'Teacher access required'], [422, 'Enter a class name and choose a supported language'],
  [503, 'Could not create class, please try again'],
] as const)('class creation explains failures (%s)', async (status, message) => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status }))
  await expect(createClass('French 101', 'fr')).rejects.toThrow(message)
})

test('network failures explain that the teacher can retry', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
  await expect(createClass('French 101', 'fr')).rejects.toThrow('Could not connect, please try again')
})

test.each([false, true])('form offers six languages and respects disabled=%s', (disabled) => {
  const html = renderToStaticMarkup(createElement(CreateClassForm, { disabled, onCreated: vi.fn(), onSessionEnded: vi.fn() }))
  expect(html.match(/<option /g)).toHaveLength(6)
  expect(html).toContain('Class name')
  expect(html).toContain('required=""')
  expect(html).toContain('<button type="submit" disabled="">Create class</button>')
  expect(html.includes('id="class-name" required="" disabled=""')).toBe(disabled)
})
