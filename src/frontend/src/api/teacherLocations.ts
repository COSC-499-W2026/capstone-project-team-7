// Lists a class's locations and uploads clue audio for them. Clips are shared by every class using a location.

import { classResponse } from './teacher'
import type { Difficulty } from '../utils/difficulties'

export interface ClassLocation {
  id: string
  building: string
  room_number: string
  audio: Record<Difficulty, boolean>
}

async function locationResponse(classId: string, options?: RequestInit, audioPath = '') {
  const res = await classResponse(options, `/${encodeURIComponent(classId)}/locations${audioPath}`)
  if (res.status === 404) throw new Error('Class or location not found')
  if (res.status === 413) throw new Error('The audio file must be 5 MB or smaller')
  if (res.status === 422) throw new Error('Please upload an MP3 file')
  if (!res.ok) throw new Error('Could not load or save clue audio, please try again')
  return res
}

export async function getClassLocations(classId: string): Promise<ClassLocation[]> {
  return (await locationResponse(classId)).json() as Promise<ClassLocation[]>
}

// The file is sent as the raw request body, the same way game photos are.
export async function uploadClueAudio(classId: string, locationId: string, file: Blob, difficulty: Difficulty): Promise<ClassLocation> {
  const audioPath = `/${encodeURIComponent(locationId)}/audio?difficulty=${difficulty}`
  const res = await locationResponse(classId, { method: 'PUT', headers: { 'Content-Type': 'audio/mpeg' }, body: file }, audioPath)
  return res.json() as Promise<ClassLocation>
}
