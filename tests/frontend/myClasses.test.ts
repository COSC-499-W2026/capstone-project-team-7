import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { afterEach, expect, test, vi } from 'vitest'
import { getProfile, type StudentClass } from '../../src/frontend/src/api/profile'
import { SessionEndedError } from '../../src/frontend/src/api/sessionEnded'
import MyClasses from '../../src/frontend/src/components/MyClasses'

const FRENCH: StudentClass = { id: 'c1', name: 'French 101', language_code: 'fr' }
const SPANISH: StudentClass = { id: 'c2', name: 'Spanish 110', language_code: 'es' }

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

function renderList(classes: StudentClass[]) {
  return renderToStaticMarkup(createElement(MyClasses, { classes }))
}

afterEach(() => {
  vi.unstubAllGlobals()
})

test('gets the profile with the enrolled classes', async () => {
  const profile = { username: 'student1', classes: [FRENCH], languages: [], profile_icon: null }
  const fetchMock = fakeBackend(200, profile)

  expect(await getProfile()).toEqual(profile)
  expect(fetchMock).toHaveBeenCalledWith('/api/student/profile')
})

test('says the session ended so the app can show the login page', async () => {
  fakeBackend(401)

  await expect(getProfile()).rejects.toThrow(SessionEndedError)
})

test('shows a general message for server problems', async () => {
  fakeBackend(503)

  await expect(getProfile()).rejects.toThrow('Could not load your classes')
  await expect(getProfile()).rejects.not.toBeInstanceOf(SessionEndedError)
})

test('each enrolled class shows its name and language', () => {
  const html = renderList([FRENCH, SPANISH])

  expect(html).toContain('My classes')
  expect(html).toContain('French 101 · French')
  expect(html).toContain('Spanish 110 · Spanish')
})

test('a student with no classes is told so', () => {
  const html = renderList([])

  expect(html).toContain("You&#x27;re not in any classes yet.")
  expect(html).not.toContain('<li>')
})
