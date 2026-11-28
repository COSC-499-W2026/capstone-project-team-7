import { SessionEndedError } from './sessionEnded'

async function adminRequest(path: string, method: string, body: object): Promise<void> {
  const res = await fetch(`/api/admin${path}`, {
    method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  }).catch(() => { throw new Error('Could not connect, please try again') })
  if (res.status === 401) throw new SessionEndedError()
  const errors: Record<number, string> = {
    400: 'Choose a registered, approved teacher',
    403: 'Admin access required',
    404: 'Class not found',
    409: 'Teacher email already approved',
    422: 'Check the email and class ID, then try again',
  }
  if (!res.ok) throw new Error(errors[res.status] ?? 'Could not save changes, please try again')
}

export function approveTeacher(email: string) {
  return adminRequest('/approved-teachers', 'POST', { email: email.trim().toLowerCase() })
}

export function reassignClass(classId: string, email: string) {
  return adminRequest(`/classes/${encodeURIComponent(classId.trim())}/teacher`, 'PATCH', {
    teacher_email: email.trim().toLowerCase(),
  })
}


export interface AdminAccount {
  id: string
  email: string
  username: string
}

export async function getOtherAdmins(): Promise<AdminAccount[]> {
  const res = await fetch('/api/admin/admins')
    .catch(() => { throw new Error('Could not load admin accounts, please try again') })
  if (res.status === 401) throw new SessionEndedError()
  if (res.status === 403) throw new Error('Admin access required')
  if (!res.ok) throw new Error('Could not load admin accounts, please try again')
  return res.json()
}

export async function deleteAdmin(id: string): Promise<void> {
  const res = await fetch(`/api/admin/admins/${encodeURIComponent(id)}`, { method: 'DELETE' })
    .catch(() => { throw new Error('Could not connect, please try again') })
  if (res.status === 401) throw new SessionEndedError()
  if (res.status === 403) throw new Error('Admin access required')
  if (res.status === 404) throw new Error('Admin account not found')
  if (res.status === 409) {
    const { detail } = await res.json()
    throw new Error(detail)
  }
  if (!res.ok) throw new Error('Could not delete the admin account, please try again')
}
