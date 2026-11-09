import { SessionEndedError } from './sessionEnded'

export interface TeacherClass {
  id: string
  name: string
  language_code: string
  class_code: string
}

export async function classResponse(options?: RequestInit, path = '') {
  const res = await fetch(`/api/teacher/classes${path}`, options)
    .catch(() => { throw new Error('Could not connect, please try again') })
  if (res.status === 401) throw new SessionEndedError()
  if (res.status === 403) throw new Error('Teacher access required')
  return res
}

export async function getTeacherClasses(): Promise<TeacherClass[]> {
  const res = await classResponse()
  if (!res.ok) throw new Error('Could not load classes, please try again')
  return res.json() as Promise<TeacherClass[]>
}

export async function createClass(name: string, language_code: string): Promise<TeacherClass> {
  const res = await classResponse({
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: name.trim(), language_code }),
  })
  if (res.status === 422) throw new Error('Enter a class name and choose a supported language')
  if (!res.ok) throw new Error('Could not create class, please try again')
  return res.json() as Promise<TeacherClass>
}

export interface RosterStudent {
  student_id: string
  first_name: string
  last_name: string
  student_number: string
}

async function rosterResponse(classId: string, options?: RequestInit, studentId?: string) {
  const path = `/${encodeURIComponent(classId)}/students${studentId ? `/${encodeURIComponent(studentId)}` : ''}`
  const res = await classResponse(options, path)
  if (res.status === 404) throw new Error('Class or student not found')
  if (res.status === 409) throw new Error('Student already enrolled')
  if (res.status === 422) throw new Error('Check the student number and try again')
  if (!res.ok) throw new Error('Could not load or update the roster, please try again')
  return res
}

export async function getClassRoster(classId: string): Promise<RosterStudent[]> {
  return (await rosterResponse(classId)).json() as Promise<RosterStudent[]>
}

export async function addStudent(classId: string, studentNumber: string): Promise<void> {
  await rosterResponse(classId, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ student_number: studentNumber.trim() }),
  })
}

export async function removeStudent(classId: string, studentId: string): Promise<void> {
  await rosterResponse(classId, { method: 'DELETE' }, studentId)
}
