import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import CreateAccountPage, { passwordProblem } from '../../src/frontend/src/CreateAccountPage'

test('a long enough password that matches has no problem', () => {
  expect(passwordProblem('password123', 'password123')).toBe('')
})

test('a password shorter than 8 characters is rejected', () => {
  expect(passwordProblem('short', 'short')).toBe('Your password needs at least 8 characters.')
})

test('passwords that do not match are rejected', () => {
  expect(passwordProblem('password123', 'password124')).toBe("Your passwords don't match.")
})

test('the page asks for every field the backend needs', () => {
  const html = renderToStaticMarkup(createElement(CreateAccountPage, { onBackToLogin: () => {} }))
  for (const field of ['First name', 'Last name', 'Student number', 'Username', 'Email', 'Password', 'Confirm password']) {
    expect(html).toContain(field)
  }
  expect(html).toContain('aria-label="Back to login"')
})
