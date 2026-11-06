// Asks the backend who is logged in, so a page refresh doesn't log the user out.

export interface CurrentUser {
  email: string
  first_name: string
  role: string
  redirect_to: string
}

// Returns null when nobody is logged in (or the check fails), so the login page shows.
export async function getCurrentUser(): Promise<CurrentUser | null> {
  try {
    const res = await fetch('/api/auth/me')
    if (!res.ok) return null
    return (await res.json()) as CurrentUser
  } catch {
    return null
  }
}
