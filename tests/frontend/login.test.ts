import { afterEach, expect, test, vi } from 'vitest'
import { login } from '../../src/frontend/src/api/login'

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

test('sends email and password to the login endpoint', async () => {
  const fetchMock = fakeBackend(200, { role: 'student', redirect_to: '/student/dashboard' })

  await login('sam@student.ubc.ca', 'secret123')

  expect(fetchMock).toHaveBeenCalledWith('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: 'sam@student.ubc.ca', password: 'secret123' }),
  })
})

test('returns the role on success', async () => {
  fakeBackend(200, { role: 'student', redirect_to: '/student/dashboard' })

  const result = await login('sam@student.ubc.ca', 'secret123')

  expect(result.role).toBe('student')
})

test('wrong email or password shows a clear message', async () => {
  fakeBackend(401)

  await expect(login('sam@student.ubc.ca', 'wrong')).rejects.toThrow('Wrong email or password')
})

test('server problems show a general message', async () => {
  fakeBackend(503)

  await expect(login('sam@student.ubc.ca', 'secret123')).rejects.toThrow('Something went wrong')
})