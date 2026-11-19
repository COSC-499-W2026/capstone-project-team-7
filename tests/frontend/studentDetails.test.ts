import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { afterEach, expect, test, vi } from 'vitest'
import { getProfile } from '../../src/frontend/src/api/profile'
import StudentDashboard, { welcomeText } from '../../src/frontend/src/pages/StudentDashboard'

// Pretend to be the backend so the tests don't need a real server.
function fakeBackend(status: number, body: unknown = {}) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => {
  vi.unstubAllGlobals()
})

test('the profile includes the username and student number from the backend', async () => {
  fakeBackend(200, { username: 'learner', student_number: '12345678', classes: [], languages: [], profile_icon: null })

  const profile = await getProfile()

  expect(profile.username).toBe('learner')
  expect(profile.student_number).toBe('12345678')
})

test('the welcome text uses the username', () => {
  expect(welcomeText('learner')).toBe('Welcome @learner')
})

test('the dashboard shows no name or student number before the profile has loaded', () => {
  fakeBackend(200, [])
  const noop = () => {}
  const html = renderToStaticMarkup(createElement(StudentDashboard, {
    onOpenGame: noop, onOpenStore: noop, onLogout: noop, onOpenBadges: noop, onOpenLeaderboard: noop,
  }))

  expect(html).toContain('Student dashboard')
  expect(html).not.toContain('Welcome @')
  expect(html).not.toContain('Student number:')
})
