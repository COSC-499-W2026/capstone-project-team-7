import { useEffect, useRef, useState, type FormEvent } from 'react'
import { approveTeacher, deleteAdmin, getOtherAdmins, reassignClass, type AdminAccount } from '../api/admin'
import { logout } from '../api/logout'
import { SessionEndedError } from '../api/sessionEnded'

export default function AdminDashboard({ onLogout }: { onLogout: () => void }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [admins, setAdmins] = useState<AdminAccount[]>([])
  const [adminListStatus, setAdminListStatus] = useState('Loading admin accounts…')
  const inFlight = useRef(false)
  const active = useRef(true)

  useEffect(() => {
    active.current = true
    return () => { active.current = false }
  }, [])

  useEffect(() => {
    let current = true
    getOtherAdmins().then((accounts) => {
      if (!current) return
      setAdmins(accounts)
      setAdminListStatus(accounts.length ? '' : 'There are no other admin accounts.')
    }).catch((err) => {
      if (!current) return
      if (err instanceof SessionEndedError) onLogout()
      else setAdminListStatus((err as Error).message)
    })
    return () => { current = false }
  }, [onLogout])

  async function run(action: () => Promise<void>, success: string, form?: HTMLFormElement) {
    if (inFlight.current) return
    inFlight.current = true
    setBusy(true)
    setError('')
    setNotice('')
    try {
      await action()
      if (!active.current) return
      if (form) { form.reset(); setNotice(success) }
      else onLogout()
    } catch (err) {
      if (!active.current) return
      if (err instanceof SessionEndedError) onLogout()
      else setError(err instanceof TypeError ? 'Could not connect, please try again' : (err as Error).message)
    } finally {
      inFlight.current = false
      if (active.current) setBusy(false)
    }
  }

  function submit(event: FormEvent<HTMLFormElement>, reassign = false) {
    event.preventDefault()
    const form = event.currentTarget
    const data = new FormData(form)
    const email = String(data.get('email'))
    void run(() => reassign ? reassignClass(String(data.get('classId')), email) : approveTeacher(email),
      reassign ? 'Class reassigned. Enrollments and progress are preserved.' : 'Teacher email approved for signup.', form)
  }

  function submitDeletion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = event.currentTarget
    const id = new FormData(form).get('adminId')
    const admin = admins.find((account) => account.id === id)
    if (!admin || !window.confirm(`Permanently delete ${admin.email}?`)) return
    void run(async () => {
      await deleteAdmin(admin.id)
      if (!active.current) return
      setAdmins((accounts) => accounts.filter((account) => account.id !== admin.id))
      if (admins.length === 1) setAdminListStatus('There are no other admin accounts.')
    }, 'Admin account deleted.', form)
  }

  return (
    <main>
      <h1>Admin dashboard</h1>
      {error && <p role="alert">{error}</p>}
      {notice && <p role="status">{notice}</p>}
      {busy && <p role="status">Saving...</p>}
      <form onSubmit={(event) => submit(event)}>
        <fieldset disabled={busy}>
          <legend>Approve teacher signup</legend>
          <p>Approve an email before the teacher creates their account.</p>
          <label>Teacher email <input name="email" type="email" required /></label>{' '}
          <button type="submit">Approve email</button>
        </fieldset>
      </form>
      <form onSubmit={(event) => submit(event, true)}>
        <fieldset disabled={busy}>
          <legend>Reassign a class</legend>
          <p>The new teacher must have a registered, approved account. Enrollments and progress are kept.</p>
          <p><label>Class ID <input name="classId" required placeholder="Class UUID" /></label></p>
          <label>New teacher email <input name="email" type="email" required /></label>{' '}
          <button type="submit">Reassign class</button>
        </fieldset>
      </form>
      <form onSubmit={submitDeletion}>
        <fieldset disabled={busy || !admins.length}>
          <legend>Delete an admin account</legend>
          <label>Admin account{' '}
            <select name="adminId" defaultValue="" required>
              <option value="">Choose an admin</option>
              {admins.map((admin) => <option key={admin.id} value={admin.id}>{admin.username} ({admin.email})</option>)}
            </select>
          </label>{' '}
          <button type="submit">Delete admin</button>
        </fieldset>
        {adminListStatus && <p role="status">{adminListStatus}</p>}
      </form>
      <p><button disabled={busy} onClick={() => void run(logout, '')}>Log out</button></p>
    </main>
  )
}
