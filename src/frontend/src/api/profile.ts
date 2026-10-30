// Asks the backend for the logged-in student's profile, including the classes they're enrolled in.

import { SessionEndedError } from './sessionEnded'

export interface StudentClass {
  id: string
  name: string
  language_code: string
}

export interface StudentProfile {
  username: string
  classes: StudentClass[]
  languages: { code: string; name: string }[]
  profile_icon: string | null
}

export async function getProfile(): Promise<StudentProfile> {
  const res = await fetch('/api/student/profile')

  if (res.status === 401) throw new SessionEndedError()
  if (!res.ok) throw new Error('Could not load your classes, please try again')

  return res.json() as Promise<StudentProfile>
}
