// Asks the backend for the logged-in student's profile, including the classes they're enrolled in.

import { apiRequest } from './request'

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
  const res = await apiRequest('/api/student/profile', undefined, { fallback: 'Could not load your classes, please try again' })
  return res.json() as Promise<StudentProfile>
}
