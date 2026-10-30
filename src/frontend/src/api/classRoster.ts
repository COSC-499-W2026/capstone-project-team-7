import { SessionEndedError } from './sessionEnded'

export interface RosterStudent {
  student_id: string
  username: string
  first_name: string
  last_name: string
  student_number: string
}

export async function getClassRoster(classId: string): Promise<RosterStudent[]> {
  const res = await fetch(`/api/teacher/classes/${encodeURIComponent(classId)}/students`)
  if (res.status === 401) throw new SessionEndedError()
  if (res.status === 403) throw new Error('Teacher access required')
  if (res.status === 404) throw new Error('Class not found')
  if (!res.ok) throw new Error('Could not load students, please try again')
  return res.json() as Promise<RosterStudent[]>
}
