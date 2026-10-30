import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { afterEach, expect, test, vi } from 'vitest'
import { signup, signupAndLogin } from '../../src/frontend/src/api/signup'
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

test('a long username says how long it can be', async () => {
  fakeBackend(422, { detail: [{ type: 'string_too_long', loc: ['body', 'username'] }] })

  await expect(signup({ ...info, username: 'a'.repeat(51) })).rejects.toThrow('Username must be 50 characters or fewer.')
})

test('a long student number says how long it can be', async () => {
  fakeBackend(422, { detail: [{ type: 'string_too_long', loc: ['body', 'student_number'] }] })

  await expect(signup({ ...info, student_number: '1'.repeat(31) })).rejects.toThrow('Student number must be 30 characters or fewer.')
})

test('a blank field still asks to fill in every field', async () => {
  fakeBackend(422, { detail: [{ type: 'string_too_short', loc: ['body', 'username'] }] })

  await expect(signup({ ...info, username: '   ' })).rejects.toThrow('Please fill in every field.')
})

test('server problems show a general message', async () => {
  fakeBackend(503)

  await expect(signup(info)).rejects.toThrow('Something went wrong')
})

// Pretend to be the backend for signup, then login.
function fakeSignupThenLogin(signupStatus: number, loginStatus: number) {
  const reply = (status: number, body: unknown) => ({
    ok: status >= 200 && status < 300, status, json: () => Promise.resolve(body),
  })
  const fetchMock = vi.fn()
    .mockResolvedValueOnce(reply(signupStatus, {}))
    .mockResolvedValueOnce(reply(loginStatus, { role: 'student', redirect_to: '/student' }))
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

test('a new account is logged straight in with the same email and password', async () => {
  const fetchMock = fakeSignupThenLogin(201, 200)

  await expect(signupAndLogin(info)).resolves.toEqual({ role: 'student', redirect_to: '/student' })
  expect(fetchMock).toHaveBeenLastCalledWith('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: info.email, password: info.password }),
  })
})

test('if the automatic login fails the account is still created and they go to the login page', async () => {
  const fetchMock = fakeSignupThenLogin(201, 503)

  await expect(signupAndLogin(info)).resolves.toBeNull()
  expect(fetchMock).toHaveBeenNthCalledWith(1, '/api/auth/student/signup', expect.anything())
  expect(fetchMock).toHaveBeenCalledTimes(2)
})

test('if signup fails it never tries to log in', async () => {
  const fetchMock = fakeSignupThenLogin(409, 200)

  await expect(signupAndLogin(info)).rejects.toThrow('That email, username or student number is already in use.')
  expect(fetchMock).toHaveBeenCalledTimes(1)
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
