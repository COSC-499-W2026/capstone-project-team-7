import { afterEach, expect, test, vi } from 'vitest'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { assignHunt, deleteHunt, getAssignedHunts, getHuntBuildings, hideOverdue, startAssignedHunt } from '../../src/frontend/src/api/assignHunt'
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

test('sends the selected building and an empty due date as null', async () => {
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 201, json: async () => ({}) })
  vi.stubGlobal('fetch', fetchMock)
  await assignHunt('c1', 'basic', '', 'COM')
  expect(fetchMock.mock.calls[0][1].body).toBe(JSON.stringify({ difficulty: 'basic', due_date: null, building: 'COM' }))
})

test('expired sessions request a return to login', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 401 }))
  await expect(assignHunt('c1', 'basic', '')).rejects.toThrow(SessionEndedError)
})

test.each([
  [403, "You can't assign hunts to this class"],
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
  expect(html.match(/<option /g)).toHaveLength(4)
  expect(html).toContain('type="date"')
  expect(html).toContain('id="hunt-building"')
  expect(html).toContain('<button type="submit" disabled="">Assign hunt</button>')
})

test('lists the hunts already assigned to the class', async () => {
  const hunts = [{ id: 'h1', difficulty: 'expert', due_date: '2026-12-01', assigned_at: '2026-11-05T18:00:00Z' }]
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => hunts })
  vi.stubGlobal('fetch', fetchMock)
  expect(await getAssignedHunts('c1')).toEqual(hunts)
  expect(fetchMock).toHaveBeenCalledWith('/api/teacher/classes/c1/hunts')
})

test('an expired session while listing hunts requests a return to login', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 401 }))
  await expect(getAssignedHunts('c1')).rejects.toThrow(SessionEndedError)
})

test.each([
  [403, "You can't see hunts for this class"], [404, "You can't see hunts for this class"],
  [503, 'Could not load assigned hunts, please try again'],
] as const)('listing hunts explains failures (%s)', async (status, message) => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status }))
  await expect(getAssignedHunts('c1')).rejects.toThrow(message)
})

test('network failures while listing hunts explain that the teacher can retry', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
  await expect(getAssignedHunts('c1')).rejects.toThrow('Could not load assigned hunts, please try again')
})

test('form has a currently assigned section that starts by loading', () => {
  const html = renderToStaticMarkup(createElement(AssignHuntForm, { classId: 'c1', disabled: false, onSessionEnded: vi.fn() }))
  expect(html).toContain('<h3>Currently assigned</h3>')
  expect(html).toContain('Loading hunts...')
})

test('removes a hunt from the class', async () => {
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 204 })
  vi.stubGlobal('fetch', fetchMock)
  await deleteHunt('c1', 'h1')
  expect(fetchMock).toHaveBeenCalledWith('/api/teacher/classes/c1/hunts/h1', { method: 'DELETE' })
})

test('an expired session while removing a hunt requests a return to login', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 401 }))
  await expect(deleteHunt('c1', 'h1')).rejects.toThrow(SessionEndedError)
})

test.each([
  [404, 'That hunt was already removed'], [503, 'Could not remove the hunt, please try again'],
] as const)('removing a hunt explains failures (%s)', async (status, message) => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status }))
  await expect(deleteHunt('c1', 'h1')).rejects.toThrow(message)
})

test('network failures while removing a hunt explain that the teacher can retry', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
  await expect(deleteHunt('c1', 'h1')).rejects.toThrow('Could not remove the hunt, please try again')
})

test('past-due hunts are hidden; hunts due today, later or with no due date are kept', () => {
  const hunt = (id: string, due_date: string | null) => ({ id, difficulty: 'basic', due_date, assigned_at: '2026-11-01T00:00:00Z' })
  const hunts = [hunt('past', '2026-11-04'), hunt('today', '2026-11-05'), hunt('later', '2026-12-01'), hunt('none', null)]
  expect(hideOverdue(hunts, '2026-11-05').map((h) => h.id)).toEqual(['today', 'later', 'none'])
})

test('past-due hunts are hidden until the teacher ticks the box', () => {
  const html = renderToStaticMarkup(createElement(AssignHuntForm, { classId: 'c1', disabled: false, onSessionEnded: vi.fn() }))
  expect(html).toContain('type="checkbox"')
  expect(html).not.toContain('checked')
  expect(html).toContain('Show past-due hunts')
})


test('shows the server error when the selected building has too few ready rooms', async () => {
  const detail = "Choose a building with at least 5 ready locations for this class's language."
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 409, json: async () => ({ detail }) }))
  await expect(assignHunt('c1', 'basic', '', 'LIB')).rejects.toThrow(detail)
})


test('loads the buildings for the selected class', async () => {
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ['COM', 'LIB'] })
  vi.stubGlobal('fetch', fetchMock)
  expect(await getHuntBuildings('c1')).toEqual(['COM', 'LIB'])
  expect(fetchMock).toHaveBeenCalledWith('/api/teacher/classes/c1/hunt-buildings')
})

test('reports invalid due dates separately from invalid building selections', async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ status: 422, json: async () => ({ detail: [{ loc: ['body', 'due_date'] }] }) })
    .mockResolvedValueOnce({ status: 422, json: async () => ({ detail: [{ loc: ['body'] }] }) })
  vi.stubGlobal('fetch', fetchMock)
  await expect(assignHunt('c1', 'basic', '2000-01-01', 'COM')).rejects.toThrow('Choose a valid due date')
  await expect(assignHunt('c1', 'basic', '')).rejects.toThrow('Check the difficulty and building selection')
})


test('starts a game using the assigned hunt ID', async () => {
  const game = { game_id: 'g1', language_code: 'fr', difficulty: 'basic', current_position: 1, total_locations: 5 }
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 201, json: async () => game })
  vi.stubGlobal('fetch', fetchMock)
  await expect(startAssignedHunt('h1')).resolves.toEqual(game)
  expect(fetchMock).toHaveBeenCalledWith('/api/student/hunts/h1/start', { method: 'POST' })
})

test('reports when the assigned building no longer has enough ready locations', async () => {
  const detail = 'Not enough ready locations in this building for this hunt'
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ status: 409, json: async () => ({ detail }) }))
  await expect(startAssignedHunt('h1')).rejects.toThrow(detail)
})
