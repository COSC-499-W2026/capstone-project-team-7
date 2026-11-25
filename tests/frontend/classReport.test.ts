import { createElement, isValidElement, type ReactElement, type ReactNode } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { afterEach, expect, test, vi } from 'vitest'
import { SessionEndedError } from '../../src/frontend/src/api/sessionEnded'
import { getClassReport, getClassReportCsv, type ClassReport } from '../../src/frontend/src/api/teacherReport'
import ClassReportView, { readableTime } from '../../src/frontend/src/components/ClassReportView'

const REPORT: ClassReport = {
  students: [{
    student_id: 's1', first_name: 'Ana', last_name: 'Lee', username: 'analee', total_points: 300,
    difficulties_completed: ['basic', 'expert'], games_finished: 2, total_game_seconds: 960, fastest_game_seconds: 750,
    locations_completed: 3, locations_skipped: 2,
    clue_plays: [{ building: 'EME', room_number: '101', plays: 5 }, { building: 'EME', room_number: '102', plays: 1 }],
  }, {
    student_id: 's2', first_name: 'Ben', last_name: 'Ng', username: 'benng', total_points: 0,
    difficulties_completed: [], games_finished: 0, total_game_seconds: 0, fastest_game_seconds: 'No games completed yet',
    locations_completed: 0, locations_skipped: 0, clue_plays: [],
  }],
  hardest_levels: {
    most_skipped: [{ building: 'EME', room_number: '103', difficulty: 'basic', count: 2 }],
    most_replayed: [{ building: 'EME', room_number: '101', difficulty: 'expert', count: 5 }],
    most_attempts: [],
  },
}

type ViewProps = Parameters<typeof ClassReportView>[0]
const PROPS: ViewProps = { classTitle: 'French 101', report: REPORT, error: '', busy: false, onDownload: () => {}, onBack: () => {} }

function render(changes: Partial<ViewProps> = {}) {
  return renderToStaticMarkup(createElement(ClassReportView, { ...PROPS, ...changes }))
}

// ClassReportView has no hooks, so calling it directly gives the element tree without needing a browser.
function findButton(props: ViewProps, label: string) {
  let found: ReactElement<{ onClick: () => void }> | undefined
  const walk = (node: ReactNode) => {
    if (Array.isArray(node)) return node.forEach(walk)
    if (!isValidElement<{ children?: ReactNode }>(node)) return
    if (node.type === 'button' && node.props.children === label) found = node as typeof found
    walk(node.props.children)
  }
  walk(ClassReportView(props))
  return found!
}

// Pretend to be the backend so the tests don't need a real server.
function fakeBackend(status: number, body: unknown = {}, headers: Record<string, string> = {}) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300, status,
    json: () => Promise.resolve(body), blob: () => Promise.resolve(new Blob(['csv'])),
    headers: new Headers(headers),
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => vi.unstubAllGlobals())

test('gets the report for the class', async () => {
  const fetchMock = fakeBackend(200, REPORT)
  expect(await getClassReport('c1')).toEqual(REPORT)
  expect(fetchMock).toHaveBeenCalledWith('/api/teacher/classes/c1/report', undefined)
})

test('the table shows one row per student', () => {
  const html = render()
  expect(html.match(/<tbody><tr>|<\/tr><tr>/g)).toHaveLength(2)
  for (const text of ['Ana Lee', 'analee', '300', 'Basic, Expert', 'EME 101: 5', 'EME 102: 1', 'Ben Ng', 'benng']) {
    expect(html).toContain(text)
  }
})

test('times are shown as minutes and seconds, not raw seconds', () => {
  expect(readableTime(750)).toBe('12m 30s')
  expect(readableTime(3725)).toBe('1h 2m 5s')
  expect(readableTime('No games completed yet')).toBe('No games completed yet')
  const html = render()
  expect(html).toContain('16m 0s')
  expect(html).toContain('12m 30s')
  expect(html).not.toContain('>960<')
})

test('the hardest levels show all three lists', () => {
  const html = render()
  for (const text of ['Hardest levels', 'Most skipped', 'EME 103 · Basic · 2', 'Most replayed audio',
    'EME 101 · Expert · 5', 'Most photo attempts', 'None yet.']) expect(html).toContain(text)
})

test('a class with no students shows a message instead of the table', () => {
  const html = render({ report: { ...REPORT, students: [] } })
  expect(html).toContain('No students in this class yet.')
  expect(html).not.toContain('<table')
})

test('a failed request shows its error message', async () => {
  fakeBackend(403)
  await expect(getClassReport('c1')).rejects.toThrow('Teacher access required')
  fakeBackend(404)
  await expect(getClassReport('c1')).rejects.toThrow('Class not found')
  fakeBackend(401)
  await expect(getClassReport('c1')).rejects.toThrow(SessionEndedError)

  const html = render({ report: null, error: 'Teacher access required' })
  expect(html).toContain('role="alert"')
  expect(html).toContain('Teacher access required')
  expect(html).not.toContain('Loading report...')
})

test('the Download CSV button asks the CSV endpoint for the file', async () => {
  const onDownload = vi.fn()
  findButton({ ...PROPS, onDownload }, 'Download CSV').props.onClick()
  expect(onDownload).toHaveBeenCalledOnce()

  const fetchMock = fakeBackend(200, {}, { 'Content-Disposition': 'attachment; filename="French-101-report-2026-11-25.csv"' })
  const { filename } = await getClassReportCsv('c1')
  expect(fetchMock).toHaveBeenCalledWith('/api/teacher/classes/c1/report.csv', undefined)
  expect(filename).toBe('French-101-report-2026-11-25.csv')
})
