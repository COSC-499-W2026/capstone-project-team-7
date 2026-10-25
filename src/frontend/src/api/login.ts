// Sends the email and password to the backend login endpoint.
// The backend sets a login cookie, so later requests know who the user is.

export interface LoginResult {
  role: string
  redirect_to: string
}

export async function login(email: string, password: string): Promise<LoginResult> {
  const res = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })

  if (res.status === 401) throw new Error('Wrong email or password')
  if (!res.ok) throw new Error('Something went wrong, please try again')

  return res.json() as Promise<LoginResult>
}