import { afterEach, expect, test, vi } from 'vitest'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { assignHunt } from '../../src/frontend/src/api/assignHunt'
import HuntClipChoices, { clipChoices, roomsWithClips } from '../../src/frontend/src/components/HuntClipChoices'

afterEach(() => vi.unstubAllGlobals())

function ownClip(id: string, room: string, difficulty: 'basic' | 'advanced' | 'expert', label = 'Café clue') {
  return { id, location_id: `l-${room}`, building: 'COM', room_number: room, difficulty, label,
           description: null, created_at: '2026-11-26T10:00:00Z' }
}

const clips = [
  ownClip('k1', '316', 'expert'), ownClip('k2', '316', 'expert', 'Quiet clue'),
  ownClip('k3', '201', 'expert'), ownClip('k4', '105', 'basic'),
]

function render(difficulty: string, picks = {}) {
  return renderToStaticMarkup(createElement(HuntClipChoices, { clips, difficulty, picks, disabled: false, onChange: vi.fn() }))
}

test('groups own clips by room for the chosen difficulty, sorted by room', () => {
  expect(roomsWithClips(clips, 'expert').map((room) => room.map((clip) => clip.id))).toEqual([['k3'], ['k1', 'k2']])
  expect(roomsWithClips(clips, 'basic').map((room) => room[0].room_number)).toEqual(['105'])
})

test('only rooms with an own clip for the difficulty show a choice', () => {
  const html = render('expert', { 'l-316': 'k2' })
  expect(html).toContain('<legend>Clips for this hunt</legend>')
  expect(html.match(/<select /g)).toHaveLength(2)
  expect(html).toContain('<option value="" selected="">Default clip</option><option value="k3">Café clue</option>')
  expect(html).toContain('<option value="k1">Café clue</option><option value="k2" selected="">Quiet clue</option>')
  expect(html).not.toContain('COM 105')
})

test('no own clips for the difficulty shows no choices', () => {
  expect(render('advanced')).toBe('')
  expect(roomsWithClips([], 'expert')).toEqual([])
})

test('only rooms set to an own clip are sent', () => {
  expect(clipChoices({ 'l-316': 'k2', 'l-201': '' })).toEqual([{ location_id: 'l-316', clip_id: 'k2' }])
  expect(clipChoices({})).toEqual([])
})

test('assigning a hunt sends the clip choices', async () => {
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 201, json: async () => ({}) })
  vi.stubGlobal('fetch', fetchMock)
  await assignHunt('c1', 'expert', '', [{ location_id: 'l-316', clip_id: 'k2' }])
  expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
    difficulty: 'expert', due_date: null, clips: [{ location_id: 'l-316', clip_id: 'k2' }],
  })
})

test('a clip the hunt cannot use shows the server message', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: false, status: 422, json: async () => ({ detail: "Your clip for COM 316 can't be used in this hunt" }),
  }))
  await expect(assignHunt('c1', 'expert', '', [{ location_id: 'l-316', clip_id: 'k2' }]))
    .rejects.toThrow("Your clip for COM 316 can't be used in this hunt")
})

test('a bad due date still shows the due date message', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 422, json: async () => ({ detail: [{ loc: ['body', 'due_date'] }] }) }))
  await expect(assignHunt('c1', 'basic', '2020-01-01')).rejects.toThrow("Due date can't be in the past")
})
