import { afterEach, expect, test, vi } from 'vitest'
import { getBadges, type Badge } from '../../src/frontend/src/api/badges'
import { SessionEndedError } from '../../src/frontend/src/api/sessionEnded'
import { badgeDescription, badgeStyle, badgeTile, earnedText } from '../../src/frontend/src/pages/BadgesPage'

const EARNED: Badge = { id: 'fr_basic', name: 'Baguette Buddy', language: 'fr', earned: true, earned_at: '2026-11-01T18:00:00Z' }
const LOCKED: Badge = { id: 'es_advanced', name: 'Windmill Whiz', language: 'es', earned: false, earned_at: null }

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

afterEach(() => vi.unstubAllGlobals())

test('gets the badge list', async () => {
  const fetchMock = fakeBackend(200, [EARNED, LOCKED])
  expect(await getBadges()).toEqual([EARNED, LOCKED])
  expect(fetchMock).toHaveBeenCalledWith('/api/student/badges')
})

test('says the session ended so the app can show the login page', async () => {
  fakeBackend(401)
  await expect(getBadges()).rejects.toThrow(SessionEndedError)
})

test('shows a general message for server problems', async () => {
  fakeBackend(503)
  await expect(getBadges()).rejects.toThrow('Could not load your badges')
  await expect(getBadges()).rejects.not.toBeInstanceOf(SessionEndedError)
})

test('each badge id points to the right tile, or none if it is not in the picture', () => {
  expect(badgeTile('fr_first_hunt')).toEqual({ row: 0, column: 0 })
  expect(badgeTile('es_advanced')).toEqual({ row: 1, column: 2 })
  expect(badgeTile('ko_master')).toEqual({ row: 5, column: 4 })
  expect(badgeTile('polyglot')).toEqual({ row: 6, column: 0 })
  expect(badgeTile('it_basic')).toBeNull()
  expect(badgeStyle({ ...LOCKED, id: 'it_basic' }).backgroundImage).toBeUndefined()
})

test('locked badges are grey and faded, earned badges are not', () => {
  expect(badgeStyle(LOCKED)).toMatchObject({ filter: 'grayscale(1)', opacity: 0.4, backgroundPosition: '-320px -202px' })
  expect(badgeStyle(EARNED).filter).toBeUndefined()
  expect(earnedText([EARNED, LOCKED, { ...LOCKED, id: 'polyglot' }])).toBe("You've earned 1 of 3 badges")
})

test('each badge says what it is for', () => {
  expect(badgeDescription({ ...EARNED, id: 'fr_first_hunt' })).toBe('Complete a full game in French on any difficulty')
  expect(badgeDescription(LOCKED)).toBe('Find every Spanish location on Advanced difficulty (across any number of games)')
  expect(badgeDescription({ ...LOCKED, id: 'ko_master', language: 'ko' })).toContain('every Korean location on all three')
  expect(badgeDescription({ ...LOCKED, id: 'polyglot', language: null })).toBe('Complete a full game in every language')
})
