// The checks every API call repeats: no connection, an ended session (401) and failed requests.

import { SessionEndedError } from './sessionEnded'

export interface RequestErrors {
  fallback: string
  statuses?: Record<number, string>
  offline?: string
  // Show the backend's own message when it sends one, e.g. why a photo was rejected.
  useDetail?: boolean
}

async function detailOf(res: Response) {
  const body = await res.json().catch(() => null)
  return typeof body?.detail === 'string' ? body.detail : undefined
}

export async function apiRequest(url: string, options: RequestInit | undefined, errors: RequestErrors): Promise<Response> {
  const res = await fetch(url, options)
    .catch(() => { throw new Error(errors.offline ?? 'Could not connect, please try again') })
  if (res.status === 401) throw new SessionEndedError()
  if (!res.ok) {
    const detail = errors.useDetail ? await detailOf(res) : undefined
    throw new Error(errors.statuses?.[res.status] ?? detail ?? errors.fallback)
  }
  return res
}
