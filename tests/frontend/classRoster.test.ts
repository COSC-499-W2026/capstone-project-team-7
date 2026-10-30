import { afterEach, expect, test, vi } from 'vitest'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { getClassRoster } from '../../src/frontend/src/api/classRoster'
import { SessionEndedError } from '../../src/frontend/src/api/sessionEnded'
import ClassRoster from '../../src/frontend/src/pages/ClassRoster'
import RosterTable from '../../src/frontend/src/pages/RosterTable'

const student = { student_id: 's1', username: 'alex', first_name: 'Alex', last_name: 'Chen', student_number: '00123456' }
afterEach(() => vi.unstubAllGlobals())

function fakeBackend(status: number, body: unknown = []) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300, status, json: async () => body,
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

test('loads the selected class roster from the teacher endpoint', async () => {
  const fetchMock = fakeBackend(200, [student])
  expect(await getClassRoster('class-1')).toEqual([student])
  expect(fetchMock).toHaveBeenCalledWith('/api/teacher/classes/class-1/students')
})

test('switching classes requests the new class roster', async () => {
  const fetchMock = fakeBackend(200)
  await getClassRoster('class-1')
  await getClassRoster('class-2')
  expect(fetchMock).toHaveBeenLastCalledWith('/api/teacher/classes/class-2/students')
})

test('accepts an empty roster', async () => {
  fakeBackend(200)
  expect(await getClassRoster('class-1')).toEqual([])
})

test('expired sessions request a return to login', async () => {
  fakeBackend(401)
  await expect(getClassRoster('class-1')).rejects.toThrow(SessionEndedError)
})

test.each([
  [403, 'Teacher access required'], [404, 'Class not found'],
  [503, 'Could not load students, please try again'],
])('explains roster access failures (%s)', async (status, message) => {
  fakeBackend(status as number)
  await expect(getClassRoster('class-1')).rejects.toThrow(message as string)
})

test('network failures do not become empty rosters', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
  await expect(getClassRoster('class-1')).rejects.toThrow()
})

test('renders student names and numbers without dropping leading zeroes', () => {
  const html = renderToStaticMarkup(createElement(RosterTable, { students: [student] }))
  expect(html).toContain('Alex Chen')
  expect(html).toContain('00123456')
  expect(html).toContain('scope="col"')
  expect(html).not.toContain('No students enrolled')
})

test('empty rosters explain that there are no enrolled students', () => {
  const html = renderToStaticMarkup(createElement(RosterTable, { students: [] }))
  expect(html).toContain('No students enrolled in this class yet.')
  expect(html).not.toContain('<table')
})

test('roster starts with a loading status rather than an empty message', () => {
  const html = renderToStaticMarkup(createElement(ClassRoster, { classId: 'class-1', onSessionEnded: vi.fn() }))
  expect(html).toContain('role="status"')
  expect(html).toContain('Loading students…')
  expect(html).not.toContain('No students enrolled')
})
