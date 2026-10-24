// Ends the login session on the backend.

export async function logout(): Promise<void> {
  const res = await fetch('/api/auth/logout', { method: 'POST' })

  // 401 means the session had already ended, so the user is logged out either way.
  if (!res.ok && res.status !== 401) throw new Error('Could not log out, please try again')
}
