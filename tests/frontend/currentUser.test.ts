import { afterEach, expect, test, vi } from 'vitest'
import { getCurrentUser } from '../../src/frontend/src/api/currentUser'

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

test('a valid login cookie returns the logged-in user', async () => {
  const user = { email: 'sam@student.ubc.ca', first_name: 'Sam', role: 'student', redirect_to: '/student/dashboard' }
  const fetchMock = fakeBackend(200, user)

  expect(await getCurrentUser()).toEqual(user)
  expect(fetchMock).toHaveBeenCalledWith('/api/auth/me')
})

test('no login or an expired login returns nobody', async () => {
  fakeBackend(401)

  expect(await getCurrentUser()).toBeNull()
})

test('a server problem returns nobody so the login page still shows', async () => {
  fakeBackend(503)

  expect(await getCurrentUser()).toBeNull()
})

test('a network failure returns nobody so the login page still shows', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')))

  expect(await getCurrentUser()).toBeNull()
})
