// Enrols the logged-in student in the class with this code.

import { apiRequest } from './request'

export interface JoinedClass {
  id: string
  name: string
  language_code: string
}

export async function joinClass(classCode: string): Promise<JoinedClass> {
  const res = await apiRequest('/api/student/classes/join', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ class_code: classCode.trim() }),
  }, {
    statuses: {
      404: 'No class matches that code',
      409: "You're already in this class",
      422: 'Please enter a valid class code',
    },
    fallback: 'Could not join the class, please try again',
  })
  return res.json() as Promise<JoinedClass>
}
