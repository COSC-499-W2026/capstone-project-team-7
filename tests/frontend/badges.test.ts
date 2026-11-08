import { afterEach, expect, test, vi } from 'vitest'
import { getBadges, type Badge } from '../../src/frontend/src/api/badges'
import { SessionEndedError } from '../../src/frontend/src/api/sessionEnded'
import { badgeDescription, badgeSpot, badgeStyle, badgeTile, earnedText } from '../../src/frontend/src/pages/BadgesPage'

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
  expect(badgeTile('it_basic')).toBeNull()
  expect(badgeStyle({ ...LOCKED, id: 'it_basic' }).backgroundImage).toBeUndefined()
})

test('each badge is cut from the right box of its picture', () => {
  expect(badgeSpot(LOCKED)).toMatchObject({ left: 532, top: 320, width: 205, height: 254 })
  expect(badgeSpot({ ...LOCKED, id: 'ko_master' })).toMatchObject({ left: 1024, top: 1466 })
  expect(badgeSpot({ ...EARNED, id: 'polyglot' })).toMatchObject({ left: 58, top: 66, width: 460 })
  expect(badgeSpot({ ...LOCKED, id: 'polyglot' })).toMatchObject({ left: 586, top: 66, width: 460 })
})

test('locked badges are grey and faded, earned badges and locked Polyglot (its own design) are not', () => {
  expect(badgeStyle(LOCKED)).toMatchObject({ filter: 'grayscale(1)', opacity: 0.4, width: 160 })
  expect(badgeStyle(EARNED).filter).toBeUndefined()
  expect(badgeStyle({ ...LOCKED, id: 'polyglot' }, 240)).toMatchObject({ width: 240, height: 287 })
  expect(badgeStyle({ ...LOCKED, id: 'polyglot' }).filter).toBeUndefined()
  expect(earnedText([EARNED, LOCKED, { ...LOCKED, id: 'polyglot' }])).toBe("You've earned 1 of 3 badges")
})

test('each badge says what it is for', () => {
  expect(badgeDescription({ ...EARNED, id: 'fr_first_hunt' })).toBe('Complete a full game in French on any difficulty')
  expect(badgeDescription(LOCKED)).toBe('Find every Spanish location on Advanced difficulty (across any number of games)')
  expect(badgeDescription({ ...LOCKED, id: 'ko_master', language: 'ko' })).toContain('every Korean location on all three')
  expect(badgeDescription({ ...LOCKED, id: 'polyglot', language: null })).toBe('Complete a full game in every language')
})
