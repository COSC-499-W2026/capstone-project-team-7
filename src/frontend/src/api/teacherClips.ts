// A teacher's own extra clips. Only that teacher sees them; they don't replace the shared default clip.

import { classResponse } from './teacher'
import type { Difficulty } from '../utils/difficulties'

export interface OwnClip {
  id: string
  location_id: string
  building: string
  room_number: string
  difficulty: Difficulty
  label: string
  description: string | null
  created_at: string
}

export interface NewClip {
  difficulty: Difficulty
  label: string
  description?: string
}

async function detailOf(res: Response) {
  const body = await res.json().catch(() => null)
  return typeof body?.detail === 'string' ? body.detail : undefined
}

async function clipResponse(classId: string, path: string, options?: RequestInit) {
  const res = await classResponse(options, `/${encodeURIComponent(classId)}${path}`)
  if (res.status === 404) throw new Error('Class, location or clip not found')
  if (res.status === 413) throw new Error('The audio file must be 5 MB or smaller')
  // A bad file has a message; bad label or description errors are a list.
  if (res.status === 422) throw new Error(await detailOf(res) ?? 'Check the label (up to 60 characters) and description (up to 300)')
  if (!res.ok) throw new Error('Could not load or save your clips, please try again')
  return res
}

export async function getClips(classId: string): Promise<OwnClip[]> {
  return (await clipResponse(classId, '/clips')).json() as Promise<OwnClip[]>
}

// The file is the raw request body, so the clip details go in the query string.
export async function addClip(classId: string, locationId: string, file: Blob, clip: NewClip): Promise<OwnClip> {
  const params = new URLSearchParams({ difficulty: clip.difficulty, label: clip.label.trim() })
  const description = clip.description?.trim()
  if (description) params.set('description', description)
  const path = `/locations/${encodeURIComponent(locationId)}/clips?${params}`
  const res = await clipResponse(classId, path, { method: 'POST', headers: { 'Content-Type': 'audio/mpeg' }, body: file })
  return res.json() as Promise<OwnClip>
}

export async function retireClip(classId: string, clipId: string): Promise<void> {
  await clipResponse(classId, `/clips/${encodeURIComponent(clipId)}`, { method: 'DELETE' })
}

export function clipAudioUrl(classId: string, clipId: string) {
  return `/api/teacher/classes/${encodeURIComponent(classId)}/clips/${encodeURIComponent(clipId)}/audio`
}
