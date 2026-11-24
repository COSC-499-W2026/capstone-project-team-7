import { afterEach, expect, test, vi } from 'vitest'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { approveTeacher, reassignClass } from '../../src/frontend/src/api/admin'
import { SessionEndedError } from '../../src/frontend/src/api/sessionEnded'
import AdminDashboard from '../../src/frontend/src/pages/AdminDashboard'

const operations = [() => approveTeacher(' Teacher@Example.com '), () => reassignClass(' c1 ', ' Teacher@Example.com ')]
afterEach(() => vi.unstubAllGlobals())

test.each([
  { index: 0, path: '/approved-teachers', method: 'POST', body: { email: 'teacher@example.com' }, status: 201 },
  { index: 1, path: '/classes/c1/teacher', method: 'PATCH', body: { teacher_email: 'teacher@example.com' }, status: 200 },
])('admin operation $index sends normalized input', async ({ index, path, method, body, status }) => {
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, status })
  vi.stubGlobal('fetch', fetchMock)
  await expect(operations[index]()).resolves.toBeUndefined()
  expect(fetchMock).toHaveBeenCalledWith(`/api/admin${path}`, {
    method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  })
})

test.each([
  [400, 'Choose a registered, approved teacher'], [403, 'Admin access required'],
  [404, 'Class not found'], [409, 'Teacher email already approved'],
  [422, 'Check the email and class ID'], [503, 'Could not save changes'],
])('admin operations explain failure %s', async (status, message) => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status }))
  for (const operation of operations) await expect(operation()).rejects.toThrow(String(message))
})

test('expired sessions return to login', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 401 }))
  for (const operation of operations) await expect(operation()).rejects.toThrow(SessionEndedError)
})

test('network failures allow retry', async () => {
  const fetchMock = vi.fn().mockRejectedValueOnce(new TypeError('Failed to fetch'))
    .mockResolvedValueOnce({ ok: true, status: 201 })
  vi.stubGlobal('fetch', fetchMock)
  await expect(approveTeacher('teacher@example.com')).rejects.toThrow('Could not connect, please try again')
  await expect(approveTeacher('teacher@example.com')).resolves.toBeUndefined()
})

test('dashboard contains labelled required fields, separate forms and logout', () => {
  const html = renderToStaticMarkup(createElement(AdminDashboard, { onLogout: vi.fn() }))
  expect(html.match(/<form/g)).toHaveLength(2)
  expect(html.match(/type="email" required/g)).toHaveLength(2)
  for (const text of ['Admin dashboard', 'Approve email', 'Reassign class', 'Class ID', 'Log out', 'Enrollments and progress are kept.']) expect(html).toContain(text)
  expect(html).not.toContain('role="alert"')
})
