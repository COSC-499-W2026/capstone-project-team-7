import { createElement, isValidElement, type ReactElement, type ReactNode } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { afterEach, expect, test, vi } from 'vitest'
import { getOngoingGames, type OngoingGame } from '../../src/frontend/src/api/ongoingGames'
import { SessionEndedError } from '../../src/frontend/src/api/sessionEnded'
import OngoingGames, { gameLabel } from '../../src/frontend/src/components/OngoingGames'

const GAME: OngoingGame = {
  game_id: 'abc', language_code: 'fr', difficulty: 'basic', current_position: 2, total_locations: 5,
  started_at: '2026-10-29T18:00:00Z',
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

function renderList(games: OngoingGame[]) {
  return renderToStaticMarkup(createElement(OngoingGames, { games, disabled: false, onResume: () => {} }))
}

// OngoingGames has no hooks, so calling it directly gives the element tree without needing a browser.
function resumeButtons(games: OngoingGame[], onResume: (game: OngoingGame) => void, disabled = false) {
  const buttons: ReactElement<{ onClick: () => void; disabled: boolean }>[] = []
  const walk = (node: ReactNode) => {
    if (Array.isArray(node)) return node.forEach(walk)
    if (!isValidElement<{ children?: ReactNode }>(node)) return
    if (node.type === 'button') buttons.push(node as (typeof buttons)[number])
    walk(node.props.children)
  }
  walk(OngoingGames({ games, disabled, onResume }))
  return buttons
}

afterEach(() => {
  vi.unstubAllGlobals()
})

test('gets the ongoing games', async () => {
  const fetchMock = fakeBackend(200, [GAME])

  expect(await getOngoingGames()).toEqual([GAME])
  expect(fetchMock).toHaveBeenCalledWith('/api/game/ongoing')
})

test('says the session ended so the app can show the login page', async () => {
  fakeBackend(401)

  await expect(getOngoingGames()).rejects.toThrow(SessionEndedError)
})

test('shows a general message for server problems', async () => {
  fakeBackend(503)

  await expect(getOngoingGames()).rejects.toThrow('Could not load your games')
  await expect(getOngoingGames()).rejects.not.toBeInstanceOf(SessionEndedError)
})

test('each ongoing game shows its language, level and progress with a resume button', () => {
  expect(gameLabel(GAME)).toBe('French · Basic · Spot 2 of 5')
  const html = renderList([GAME, { ...GAME, game_id: 'def', difficulty: 'expert', current_position: 4 }])
  expect(html).toContain('Ongoing games')
  expect(html).toContain('French · Basic · Spot 2 of 5')
  expect(html).toContain('French · Expert · Spot 4 of 5')
  expect(html.match(/>Resume</g)).toHaveLength(2)
})

test('the list is hidden when there are no ongoing games', () => {
  expect(renderList([])).toBe('')
})

test('clicking resume opens the game that was picked', () => {
  const second = { ...GAME, game_id: 'def', current_position: 4 }
  const onResume = vi.fn()

  resumeButtons([GAME, second], onResume)[1].props.onClick()

  expect(onResume).toHaveBeenCalledOnce()
  expect(onResume).toHaveBeenCalledWith(second)
})

test('resume buttons are disabled while another game is starting', () => {
  const buttons = resumeButtons([GAME], vi.fn(), true)

  expect(buttons[0].props.disabled).toBe(true)
})
