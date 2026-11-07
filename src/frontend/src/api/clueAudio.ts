import { SessionEndedError } from './sessionEnded'

export async function getClueAudio(url: string) {
  const res = await fetch(url, { cache: 'no-store' })
  if (res.status === 401) throw new SessionEndedError()
  if (res.status === 409) throw new Error((await res.json()).detail)
  if (res.status === 404) throw new Error('Audio not found for this clue')
  if (!res.ok) throw new Error('Could not load audio, please try again')
  const value = res.headers.get('X-Audio-Plays-Remaining')
  return { audio: await res.blob(), remaining: value === 'unlimited' ? null : Number(value) }
}
