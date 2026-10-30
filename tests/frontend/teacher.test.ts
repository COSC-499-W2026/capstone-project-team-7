import { afterEach, expect, test, vi } from 'vitest'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { getTeacherClasses } from '../../src/frontend/src/api/teacher'
import { SessionEndedError } from '../../src/frontend/src/api/sessionEnded'
import TeacherDashboard from '../../src/frontend/src/pages/TeacherDashboard'

afterEach(() => vi.unstubAllGlobals())

function fakeBackend(status: number, body: unknown = []) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300, status,
    json: async () => body,
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

test('loads the signed-in teacher’s classes', async () => {
  const classes = [{ id: 'abc', name: 'French 101', language_code: 'fr', class_code: 'ABC123' }]
  const fetchMock = fakeBackend(200, classes)
  expect(await getTeacherClasses()).toEqual(classes)
  expect(fetchMock).toHaveBeenCalledWith('/api/teacher/classes')
})

test('accepts a teacher with no classes', async () => {
  fakeBackend(200)
  expect(await getTeacherClasses()).toEqual([])
})

test('expired sessions request a return to login', async () => {
  fakeBackend(401)
  await expect(getTeacherClasses()).rejects.toThrow(SessionEndedError)
})

test.each([403, 503])('explains class access failures (%s)', async (status) => {
  fakeBackend(status)
  await expect(getTeacherClasses()).rejects.toThrow(
    status === 403 ? 'Teacher access required' : 'Could not load classes, please try again',
  )
})

test('does not treat a network failure as an empty class list', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
  await expect(getTeacherClasses()).rejects.toThrow()
})

test('dashboard starts with a loading status and logout control', () => {
  const html = renderToStaticMarkup(createElement(TeacherDashboard, { onLogout: vi.fn() }))
  expect(html).toContain('Teacher dashboard')
  expect(html).toContain('role="status"')
  expect(html).toContain('Loading classes…')
  expect(html).toContain('Log out')
  expect(html).not.toContain('No classes assigned yet.')
})
