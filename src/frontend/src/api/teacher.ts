import { SessionEndedError } from './sessionEnded'

export interface TeacherClass {
  id: string
  name: string
  language_code: string
  class_code: string
}

async function classResponse(options?: RequestInit) {
  const res = await fetch('/api/teacher/classes', options)
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
