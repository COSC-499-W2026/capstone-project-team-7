import { SessionEndedError } from './sessionEnded'

export interface TeacherClass {
  id: string
  name: string
  language_code: string
  class_code: string
}

export async function getTeacherClasses(): Promise<TeacherClass[]> {
  const res = await fetch('/api/teacher/classes')
  if (res.status === 401) throw new SessionEndedError()
  if (res.status === 403) throw new Error('Teacher access required')
  if (!res.ok) throw new Error('Could not load classes, please try again')
  return res.json() as Promise<TeacherClass[]>
}
