// Asks the backend to assign a hunt to one of the teacher's classes. The class's language is used automatically.

import { SessionEndedError } from './sessionEnded'

export interface AssignedHunt {
  id: string
  class_id: string
  language_code: string
  difficulty: string
  due_date: string | null
}

// dueDate is "YYYY-MM-DD", or "" when the teacher leaves it empty.
export async function assignHunt(classId: string, difficulty: string, dueDate: string): Promise<AssignedHunt> {
  const res = await fetch(`/api/teacher/classes/${encodeURIComponent(classId)}/hunts`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ difficulty, due_date: dueDate || null }),
  }).catch(() => { throw new Error('Could not assign the hunt, please try again') })

  if (res.status === 401) throw new SessionEndedError()
  if (res.status === 422) throw new Error("Due date can't be in the past")
  if (res.status === 403 || res.status === 404) throw new Error("You can't assign hunts to this class")
  if (!res.ok) throw new Error('Could not assign the hunt, please try again')

  return res.json() as Promise<AssignedHunt>
}

export interface ClassHunt {
  id: string
  difficulty: string
  due_date: string | null
  assigned_at: string
}

// The hunts already assigned to one of the teacher's classes, newest first.
export async function getAssignedHunts(classId: string): Promise<ClassHunt[]> {
  const res = await fetch(`/api/teacher/classes/${encodeURIComponent(classId)}/hunts`)
    .catch(() => { throw new Error('Could not load assigned hunts, please try again') })

  if (res.status === 401) throw new SessionEndedError()
  if (res.status === 403 || res.status === 404) throw new Error("You can't see hunts for this class")
  if (!res.ok) throw new Error('Could not load assigned hunts, please try again')

  return res.json() as Promise<ClassHunt[]>
}

export async function deleteHunt(classId: string, huntId: string): Promise<void> {
  const res = await fetch(`/api/teacher/classes/${encodeURIComponent(classId)}/hunts/${encodeURIComponent(huntId)}`, {
    method: 'DELETE',
  }).catch(() => { throw new Error('Could not remove the hunt, please try again') })

  if (res.status === 401) throw new SessionEndedError()
  if (res.status === 404) throw new Error('That hunt was already removed')
  if (!res.ok) throw new Error('Could not remove the hunt, please try again')
}

// today is "YYYY-MM-DD", so dates compare correctly as text. Hunts with no due date never go past due.
// <Hunt extends ...> lets this work for teacher and student hunts alike: anything with a due_date.
export function hideOverdue<Hunt extends { due_date: string | null }>(hunts: Hunt[], today: string): Hunt[] {
  return hunts.filter((hunt) => !hunt.due_date || hunt.due_date >= today)
}

export interface StudentHunt {
  id: string
  class_id: string
  class_name: string
  language_code: string
  difficulty: string
  due_date: string | null
}

// The hunts teachers assigned to the logged-in student's classes, soonest due first.
export async function getStudentHunts(): Promise<StudentHunt[]> {
  const res = await fetch('/api/student/hunts')
    .catch(() => { throw new Error('Could not load your assigned hunts, please try again') })

  if (res.status === 401) throw new SessionEndedError()
  if (!res.ok) throw new Error('Could not load your assigned hunts, please try again')

  return res.json() as Promise<StudentHunt[]>
}
