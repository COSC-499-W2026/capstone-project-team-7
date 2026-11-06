import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { afterEach, expect, test, vi } from 'vitest'
import { SessionEndedError } from '../../src/frontend/src/api/sessionEnded'
import { equipIcon, getStore, redeemIcon, type Store } from '../../src/frontend/src/api/store'
import StoreView from '../../src/frontend/src/components/StoreView'

const STORE: Store = {
  balance: 120,
  icons: [
    { id: 'croissant_cutie', name: 'Croissant Cutie', price: 50, owned: true, equipped: true },
    { id: 'mac_the_macaron', name: 'Mac the Macaron', price: 100, owned: false, equipped: false },
    { id: 'speedy_escargot', name: 'Speedy Escargot', price: 150, owned: false, equipped: false },
  ],
}

// Pretend to be the backend so the tests don't need a real server.
function fakeBackend(status: number, body: unknown = {}) {
  const fetchMock = vi.fn().mockResolvedValue({ ok: status >= 200 && status < 300, status, json: async () => body })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

function renderStore(store: Store) {
  return renderToStaticMarkup(createElement(StoreView, { store, busy: false, onBuy: vi.fn(), onEquip: vi.fn() }))
}

afterEach(() => vi.unstubAllGlobals())

test('gets the coin balance and the icons', async () => {
  const fetchMock = fakeBackend(200, STORE)
  expect(await getStore()).toEqual(STORE)
  expect(fetchMock).toHaveBeenCalledWith('/api/student/store', undefined)
})

test('buying an icon posts to its redeem URL', async () => {
  const fetchMock = fakeBackend(201, { icon_id: 'mac_the_macaron', balance: 20 })
  await redeemIcon('mac_the_macaron')
  expect(fetchMock).toHaveBeenCalledWith('/api/student/store/mac_the_macaron/redeem', { method: 'POST' })
})

test('equipping an icon sends its id to the profile icon endpoint', async () => {
  const fetchMock = fakeBackend(200, { profile_icon: 'croissant_cutie' })
  await equipIcon('croissant_cutie')
  expect(fetchMock).toHaveBeenCalledWith('/api/student/profile/icon', {
    method: 'PUT', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ icon_id: 'croissant_cutie' }),
  })
})

test('an expired session requests a return to login', async () => {
  fakeBackend(401)
  await expect(getStore()).rejects.toThrow(SessionEndedError)
  await expect(redeemIcon('mac_the_macaron')).rejects.toThrow(SessionEndedError)
  await expect(equipIcon('croissant_cutie')).rejects.toThrow(SessionEndedError)
})

test.each([
  [400, "You don't have enough coins for this"], [409, 'You already own this icon'],
  [404, 'Something went wrong, please try again'], [503, 'Something went wrong, please try again'],
] as const)('buying explains failures (%s)', async (status, message) => {
  fakeBackend(status)
  await expect(redeemIcon('mac_the_macaron')).rejects.toThrow(message)
})

test('network failures show the general message', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
  await expect(getStore()).rejects.toThrow('Something went wrong, please try again')
})

test('the store shows the coin balance', () => {
  expect(renderStore(STORE)).toContain('You have 120 coins')
})

test('an icon the student can afford has a buy button', () => {
  expect(renderStore(STORE)).toContain('Buy for 100 coins</button>')
})

test('an icon the student can\'t afford is locked and says how many more coins they need', () => {
  const html = renderStore(STORE)
  expect(html).toContain('<button disabled="">Need 30 more coins</button>')
  expect(html).toMatch(/aria-label="Speedy Escargot" style="[^"]*grayscale/)
  expect(html).not.toMatch(/aria-label="Mac the Macaron" style="[^"]*grayscale/)
})

test('an owned icon can be equipped and the equipped one says so', () => {
  const owned = { ...STORE, icons: [{ ...STORE.icons[0], equipped: false }, STORE.icons[1]] }
  expect(renderStore(owned)).toContain('Equip</button>')
  expect(renderStore(STORE)).toContain('Equipped ✓')
  expect(renderStore(STORE)).not.toContain('>Equip</button>')
})
