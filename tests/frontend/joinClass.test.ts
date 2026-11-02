import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { afterEach, expect, test, vi } from 'vitest'
import { joinClass } from '../../src/frontend/src/api/joinClass'
import { SessionEndedError } from '../../src/frontend/src/api/sessionEnded'
import JoinClass, { joinedMessage } from '../../src/frontend/src/components/JoinClass'

const CLASS = { id: 'c1', name: 'French 101', language_code: 'fr' }

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

test('sends the class code to the join endpoint and returns the class', async () => {
  const fetchMock = fakeBackend(201, CLASS)

  expect(await joinClass(' abc123def456 ')).toEqual(CLASS)
  expect(fetchMock).toHaveBeenCalledWith('/api/student/classes/join', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ class_code: 'abc123def456' }),
  })
})

test('joining shows the class name', () => {
  expect(joinedMessage(CLASS.name)).toBe('You joined French 101.')
})

test('an unknown code says no class matches', async () => {
  fakeBackend(404)

  await expect(joinClass('NOPE')).rejects.toThrow('No class matches that code')
})

test('a class the student is already in says so', async () => {
  fakeBackend(409)

  await expect(joinClass('ABC123DEF456')).rejects.toThrow("You're already in this class")
})

test('an invalid code asks for a valid one', async () => {
  fakeBackend(422)

  await expect(joinClass('')).rejects.toThrow('Please enter a valid class code')
})

test('says the session ended so the app can show the login page', async () => {
  fakeBackend(401)

  await expect(joinClass('ABC123DEF456')).rejects.toThrow(SessionEndedError)
})

test('shows a general message for server problems', async () => {
  fakeBackend(503)

  await expect(joinClass('ABC123DEF456')).rejects.toThrow('Could not join the class')
  await expect(joinClass('ABC123DEF456')).rejects.not.toBeInstanceOf(SessionEndedError)
})

test('the join button is disabled until a code is typed, and codes are 12 characters at most', () => {
  const html = renderToStaticMarkup(createElement(JoinClass, { onSessionEnded: () => {} }))

  expect(html).toContain('Class code')
  expect(html).toContain('maxLength="12"')
  expect(html).toContain('disabled="">Join</button>')
})
