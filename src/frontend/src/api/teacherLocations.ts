// Lists a class's locations and uploads clue audio for them. Clips are shared by every class using a location.

import { classResponse } from './teacher'

export interface ClassLocation {
  id: string
  building: string
  room_number: string
  has_audio: boolean
}

async function locationResponse(classId: string, options?: RequestInit, locationId?: string) {
  const path = `/${encodeURIComponent(classId)}/locations${locationId ? `/${encodeURIComponent(locationId)}/audio` : ''}`
  const res = await classResponse(options, path)
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
export async function uploadClueAudio(classId: string, locationId: string, file: Blob): Promise<ClassLocation> {
  const res = await locationResponse(classId, { method: 'PUT', headers: { 'Content-Type': 'audio/mpeg' }, body: file }, locationId)
  return res.json() as Promise<ClassLocation>
}
