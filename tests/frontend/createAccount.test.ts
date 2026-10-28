import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { afterEach, expect, test, vi } from 'vitest'
import { signup } from '../../src/frontend/src/api/signup'
import CreateAccountPage from '../../src/frontend/src/pages/CreateAccountPage'
import LoginPage from '../../src/frontend/src/pages/LoginPage'

const info = {
  email: 'sam@student.ubc.ca', password: 'secret123', first_name: 'Sam',
  last_name: 'Lee', student_number: '12345678', username: 'samlee',
}

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

test('sends the student details to the signup endpoint', async () => {
  const fetchMock = fakeBackend(201, { id: 'abc', role: 'student' })

  await expect(signup(info)).resolves.toBeUndefined()
  expect(fetchMock).toHaveBeenCalledWith('/api/auth/student/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(info),
  })
})

test('an email already in use shows a clear message', async () => {
  fakeBackend(409, { detail: 'Account details already in use' })

  await expect(signup(info)).rejects.toThrow('That email, username or student number is already in use.')
})

test('a short password says how long it must be', async () => {
  fakeBackend(422, { detail: [{ loc: ['body', 'password'], msg: 'too short' }] })

  await expect(signup({ ...info, password: 'short' })).rejects.toThrow('Password must be between 8 and 72 characters.')
})

test('server problems show a general message', async () => {
  fakeBackend(503)

  await expect(signup(info)).rejects.toThrow('Something went wrong')
})

test('the login page has a create account button', () => {
  const html = renderToStaticMarkup(createElement(LoginPage, { onLogin: () => {}, onCreateAccount: () => {} }))
  expect(html).toContain('<button type="button">Create account</button>')
})

test('the login page shows the account created message', () => {
  const html = renderToStaticMarkup(createElement(LoginPage, {
    onLogin: () => {}, onCreateAccount: () => {}, notice: 'Account created! Please log in.',
  }))
  expect(html).toContain('Account created! Please log in.')
})

test('the create account page asks for every signup field and links back to login', () => {
  const html = renderToStaticMarkup(createElement(CreateAccountPage, { onCreated: () => {}, onBack: () => {} }))
  for (const id of ['first_name', 'last_name', 'username', 'student_number', 'email', 'password']) {
    expect(html).toContain(`id="${id}"`)
  }
  expect(html).toContain('Back to login')
})
