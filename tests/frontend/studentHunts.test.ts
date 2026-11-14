import { createElement, isValidElement, type ReactElement, type ReactNode } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { afterEach, expect, test, vi } from 'vitest'
import { getStudentHunts, type StudentHunt } from '../../src/frontend/src/api/assignHunt'
import { SessionEndedError } from '../../src/frontend/src/api/sessionEnded'
import AssignedHunts, { huntLabel } from '../../src/frontend/src/components/AssignedHunts'

// Far in the future so the hunt is never past due, whatever day the tests run.
const HUNT: StudentHunt = {
  id: 'h1', class_id: 'c1', class_name: 'French 101', language_code: 'fr', difficulty: 'basic', due_date: '2999-01-01',
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

function renderList(hunts: StudentHunt[]) {
  return renderToStaticMarkup(createElement(AssignedHunts, { hunts, disabled: false, onPlay: () => {} }))
}

// AssignedHunts has no hooks, so calling it directly gives the element tree without needing a browser.
function playButtons(hunts: StudentHunt[], onPlay: (hunt: StudentHunt) => void, disabled = false) {
  const buttons: ReactElement<{ onClick: () => void; disabled: boolean }>[] = []
  const walk = (node: ReactNode) => {
    if (Array.isArray(node)) return node.forEach(walk)
    if (!isValidElement<{ children?: ReactNode }>(node)) return
    if (node.type === 'button') buttons.push(node as (typeof buttons)[number])
    walk(node.props.children)
  }
  walk(AssignedHunts({ hunts, disabled, onPlay }))
  return buttons
}

afterEach(() => {
  vi.unstubAllGlobals()
})

test('gets the hunts assigned to the student', async () => {
  const fetchMock = fakeBackend(200, [HUNT])

  expect(await getStudentHunts()).toEqual([HUNT])
  expect(fetchMock).toHaveBeenCalledWith('/api/student/hunts')
})

test('says the session ended so the app can show the login page', async () => {
  fakeBackend(401)

  await expect(getStudentHunts()).rejects.toThrow(SessionEndedError)
})

test('shows a general message for server problems and network failures', async () => {
  fakeBackend(503)
  await expect(getStudentHunts()).rejects.toThrow('Could not load your assigned hunts')
  await expect(getStudentHunts()).rejects.not.toBeInstanceOf(SessionEndedError)

  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
  await expect(getStudentHunts()).rejects.toThrow('Could not load your assigned hunts')
})

test('each hunt shows its class, language, difficulty and due date, with a play button', () => {
  expect(huntLabel(HUNT)).toBe('French 101 · French · Basic · Due 2999-01-01')
  expect(huntLabel({ ...HUNT, difficulty: 'expert', due_date: null })).toBe('French 101 · French · Expert')
  const html = renderList([HUNT, { ...HUNT, id: 'h2', class_name: 'Spanish 101', language_code: 'es', due_date: null }])
  expect(html).toContain('Assigned hunts')
  expect(html).toContain('Spanish 101 · Spanish · Basic')
  expect(html.match(/>Play</g)).toHaveLength(2)
})

test('hunts past their due date are hidden; hunts with no due date always show', () => {
  const html = renderList([
    { ...HUNT, id: 'past', class_name: 'Old class', due_date: '2000-01-01' },
    { ...HUNT, id: 'none', class_name: 'No date class', due_date: null },
  ])
  expect(html).not.toContain('Old class')
  expect(html).toContain('No date class')
})

test('a friendly message shows when there are no hunts to play', () => {
  expect(renderList([])).toContain('No assigned hunts right now.')
  expect(renderList([{ ...HUNT, due_date: '2000-01-01' }])).toContain('No assigned hunts right now.')
})

test('clicking play starts the hunt that was picked', () => {
  const second = { ...HUNT, id: 'h2', language_code: 'es', difficulty: 'advanced' }
  const onPlay = vi.fn()

  playButtons([HUNT, second], onPlay)[1].props.onClick()

  expect(onPlay).toHaveBeenCalledOnce()
  expect(onPlay).toHaveBeenCalledWith(second)
})

test('play buttons are disabled while another game is starting', () => {
  expect(playButtons([HUNT], vi.fn(), true)[0].props.disabled).toBe(true)
})
