import { afterEach, expect, test, vi } from 'vitest'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { getLeaderboard } from '../../src/frontend/src/api/leaderboard'
import { SessionEndedError } from '../../src/frontend/src/api/sessionEnded'
import LeaderboardPage from '../../src/frontend/src/pages/LeaderboardPage'
import LeaderboardTable from '../../src/frontend/src/components/LeaderboardTable'

const classroom = { id: 'c1', name: 'French 101', language_code: 'fr' }
const entries = [
  { rank: 1, username: 'Alex', total_points: 150, profile_icon: 'croissant_cutie' },
  { rank: 1, username: 'Sam', total_points: 150, profile_icon: null },
  { rank: 3, username: '<Zero>', total_points: 0, profile_icon: null },
]
afterEach(() => vi.unstubAllGlobals())

test.each([{ body: entries }, { body: [] }])('loads leaderboard results including an empty list', async ({ body }) => {
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => body })
  vi.stubGlobal('fetch', fetchMock)
  expect(await getLeaderboard('c1')).toEqual(body)
  expect(fetchMock).toHaveBeenCalledWith('/api/student/classes/c1/leaderboard')
})

test.each([401, 403, 404, 422, 503])('handles leaderboard HTTP failure %s', async (status) => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status }))
  await expect(getLeaderboard('c1')).rejects.toThrow(status === 401 ? SessionEndedError : 'Could not load this leaderboard')
})

test('network failure can be retried successfully', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValueOnce(new TypeError('Failed to fetch'))
    .mockResolvedValueOnce({ ok: true, json: async () => entries }))
  await expect(getLeaderboard('c1')).rejects.toThrow('Could not connect, please try again')
  expect(await getLeaderboard('c1')).toEqual(entries)
})

test('renders ranks, scores, class caption, equipped artwork and neutral fallback', () => {
  const html = renderToStaticMarkup(createElement(LeaderboardTable, { classroom, entries }))
  expect(html).toContain('French 101 · French')
  expect(html.match(/<td>1<\/td>/g)).toHaveLength(2)
  for (const text of ['<td>3</td>', '<td>0</td>', '150', 'Alex', '&lt;Zero&gt;', 'background-image:', 'No profile icon', 'border-radius:50%']) expect(html).toContain(text)
  expect(renderToStaticMarkup(createElement(LeaderboardTable, { classroom, entries: [] }))).toContain('No students to display.')
})

test('screen initially shows loading and a back button', () => {
  const html = renderToStaticMarkup(createElement(LeaderboardPage, { onBack: vi.fn(), onSessionEnded: vi.fn() }))
  expect(html).toContain('role="status"')
  expect(html).toContain('Loading leaderboard...')
  expect(html).toContain('>Back</button>')
})
