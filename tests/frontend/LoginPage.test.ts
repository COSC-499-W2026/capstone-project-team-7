import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import LoginPage from '../../src/frontend/src/LoginPage'

function renderLoginPage() {
  return renderToStaticMarkup(createElement(LoginPage, { onCreateAccount: () => {}, onPlayAsGuest: () => {} }))
}

test('the login page has labelled email and password fields', () => {
  const html = renderLoginPage()
  expect(html).toContain('Email')
  expect(html).toContain('type="email"')
  expect(html).toContain('Password')
  expect(html).toContain('type="password"')
})

test('the login page shows all three options', () => {
  const html = renderLoginPage()
  expect(html).toContain('>Login<')
  expect(html).toContain('Create account')
  expect(html).toContain('Play as guest')
})
