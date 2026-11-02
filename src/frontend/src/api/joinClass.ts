// Enrols the logged-in student in the class with this code.

import { SessionEndedError } from './sessionEnded'

export interface JoinedClass {
  id: string
  name: string
  language_code: string
}

export async function joinClass(classCode: string): Promise<JoinedClass> {
  const res = await fetch('/api/student/classes/join', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ class_code: classCode.trim() }),
  })

  if (res.status === 401) throw new SessionEndedError()
  if (res.status === 404) throw new Error('No class matches that code')
  if (res.status === 409) throw new Error("You're already in this class")
  if (res.status === 422) throw new Error('Please enter a valid class code')
  if (!res.ok) throw new Error('Could not join the class, please try again')

  return res.json() as Promise<JoinedClass>
}
