import { afterEach, expect, test, vi } from 'vitest'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { getTeacherClasses } from '../../src/frontend/src/api/teacher'
import { SessionEndedError } from '../../src/frontend/src/api/sessionEnded'
import TeacherDashboard from '../../src/frontend/src/pages/TeacherDashboard'

afterEach(() => vi.unstubAllGlobals())

test.each([[], [{ id: 'c1', name: 'French 101', language_code: 'fr', class_code: 'ABC123' }]])('loads assigned classes, including empty results (%j)', async (classes) => {
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => classes })
  vi.stubGlobal('fetch', fetchMock)
  expect(await getTeacherClasses()).toEqual(classes)
  expect(fetchMock).toHaveBeenCalledWith('/api/teacher/classes', undefined)
})

test('expired sessions request a return to login', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 401 }))
  await expect(getTeacherClasses()).rejects.toThrow(SessionEndedError)
})

test.each([[403, 'Teacher access required'], [503, 'Could not load classes, please try again']] as const)('explains class-list failures (%s)', async (status, message) => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status }))
  await expect(getTeacherClasses()).rejects.toThrow(message)
})

test('network failures show a friendly retry message', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
  await expect(getTeacherClasses()).rejects.toThrow('Could not connect, please try again')
})

test('dashboard shows loading and logout without roster controls', () => {
  const html = renderToStaticMarkup(createElement(TeacherDashboard, { onLogout: vi.fn() }))
  for (const label of ['Teacher dashboard', 'My classes', 'Loading classes...', 'Log out']) expect(html).toContain(label)
  for (const label of ['No classes assigned yet.', 'Class roster', 'Add student', 'Remove']) expect(html).not.toContain(label)
})
