import { afterEach, expect, test, vi } from 'vitest'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { addStudent, getClassRoster, removeStudent } from '../../src/frontend/src/api/teacher'
import { SessionEndedError } from '../../src/frontend/src/api/sessionEnded'
import ClassRoster from '../../src/frontend/src/components/ClassRoster'
import RemovedStudents from '../../src/frontend/src/components/RemovedStudents'

afterEach(() => vi.unstubAllGlobals())
const student = { student_id: 's1', first_name: 'Alex', last_name: 'Chen', student_number: '00123456',
  status: 'enrolled', unenrolled_at: null }
const operations = [() => getClassRoster('c1'), () => addStudent('c1', ' 00123456 '), () => removeStudent('c1', 's1')]

test.each([
  [0, '/c1/students', undefined, 200],
  [1, '/c1/students', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ student_number: '00123456' }) }, 201],
  [2, '/c1/students/s1', { method: 'DELETE' }, 204],
] as const)('roster operation %s sends the request and accepts success', async (index, path, options, status) => {
  const json = vi.fn().mockResolvedValue([student])
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, status, json })
  vi.stubGlobal('fetch', fetchMock)
  expect(await operations[index]()).toEqual(index === 0 ? [student] : undefined)
  expect(fetchMock).toHaveBeenCalledWith(`/api/teacher/classes${path}`, options)
  if (index !== 0) expect(json).not.toHaveBeenCalled()
})

test('accepts an empty roster', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => [] }))
  expect(await getClassRoster('c1')).toEqual([])
})

test('all roster operations return expired sessions to login', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 401 }))
  for (const operation of operations) await expect(operation()).rejects.toThrow(SessionEndedError)
})

test.each([
  [403, 'Teacher access required'], [404, 'Class or student not found'], [409, 'Student already enrolled'],
  [422, 'Check the student number'], [503, 'Could not load or update the roster'],
] as const)('explains roster failures (%s)', async (status, message) => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status }))
  for (const operation of operations) await expect(operation()).rejects.toThrow(message)
})

test('network failures offer a friendly retry message', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
  for (const operation of operations) await expect(operation()).rejects.toThrow('Could not connect, please try again')
})

test('roster starts loading with enrollment disabled and explains account preservation', () => {
  const html = renderToStaticMarkup(createElement(ClassRoster, { classId: 'c1', disabled: false, onSessionEnded: vi.fn() }))
  expect(html).toContain('Loading students...')
  expect(html).toContain('role="status"')
  expect(html).toContain('<button type="submit" disabled="">Add student</button>')
  expect(html).toContain('Removing them keeps their account and class history.')
  expect(html).not.toContain('No students enrolled yet.')
  expect(html).not.toContain('Removed students')
})

test('removed students are listed with their removal date and no Remove button', () => {
  const removed = [
    { ...student, status: 'unenrolled', unenrolled_at: '2026-11-02T12:00:00Z' },
    { ...student, student_id: 's2', first_name: 'Sam', last_name: 'Lee', student_number: '00654321', status: 'unenrolled', unenrolled_at: '2026-10-20T12:00:00Z' },
  ] as const
  const html = renderToStaticMarkup(createElement(RemovedStudents, { students: [...removed] }))
  expect(html).toContain('aria-label="Removed students"')
  expect(html).toContain('Alex Chen · 00123456 · Removed 2026-11-02')
  expect(html).toContain('Sam Lee · 00654321 · Removed 2026-10-20')
  expect(html).not.toContain('<button')
})
