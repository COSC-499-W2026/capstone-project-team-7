// Asks the backend for the student's coins and the icons in the store, and buys or equips an icon.

import { SessionEndedError } from './sessionEnded'

export interface StoreIcon {
  id: string
  name: string
  price: number | null
  owned: boolean
  equipped: boolean
}

export interface Store {
  balance: number
  icons: StoreIcon[]
}

const GENERAL_ERROR = 'Something went wrong, please try again'

async function send(url: string, options?: RequestInit): Promise<Response> {
  const res = await fetch(url, options).catch(() => { throw new Error(GENERAL_ERROR) })

  if (res.status === 401) throw new SessionEndedError()
  if (res.status === 400) throw new Error("You don't have enough coins for this")
  if (res.status === 409) throw new Error('You already own this icon')
  if (!res.ok) throw new Error(GENERAL_ERROR)

  return res
}

export async function getStore(): Promise<Store> {
  return (await send('/api/student/store')).json() as Promise<Store>
}

export async function redeemIcon(iconId: string): Promise<void> {
  await send(`/api/student/store/${encodeURIComponent(iconId)}/redeem`, { method: 'POST' })
}

export async function equipIcon(iconId: string): Promise<void> {
  await send('/api/student/profile/icon', {
    method: 'PUT', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ icon_id: iconId }),
  })
}
