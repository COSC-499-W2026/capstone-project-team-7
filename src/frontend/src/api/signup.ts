// Sends a new student's details to the backend signup endpoint.

import { login, type LoginResult } from './login'

export interface SignupInfo {
  email: string
  password: string
  first_name: string
  last_name: string
  student_number: string
  username: string
}

// Turns the backend's field validation errors into one message the student can act on.
function invalidFieldMessage(detail: unknown): string {
  const field = Array.isArray(detail) ? detail[0]?.loc?.[1] : null
  if (field === 'password') return 'Password must be between 8 and 72 characters.'
  if (field === 'email') return 'Please enter a valid email.'
  return 'Please fill in every field.'
}

export async function signup(info: SignupInfo): Promise<void> {
  const res = await fetch('/api/auth/student/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(info),
  }).catch(() => { throw new Error('Something went wrong, please try again') })

  if (res.status === 409) throw new Error('That email, username or student number is already in use.')
  if (res.status === 422) {
    const body = await res.json().catch(() => null)
    throw new Error(invalidFieldMessage(body?.detail))
  }
  if (!res.ok) throw new Error('Something went wrong, please try again')
}

// Creates the account, then logs in with the same details.
// Returns null if the account was made but the login failed, so the caller can send them to the login page.
export async function signupAndLogin(info: SignupInfo): Promise<LoginResult | null> {
  await signup(info)
  return login(info.email, info.password).catch(() => null)
}
