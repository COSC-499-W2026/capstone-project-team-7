import { useEffect, useRef, useState, type FormEvent } from 'react'
import { approveTeacher, reassignClass } from '../api/admin'
import { logout } from '../api/logout'
import { SessionEndedError } from '../api/sessionEnded'

export default function AdminDashboard({ onLogout }: { onLogout: () => void }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const inFlight = useRef(false)
  const active = useRef(true)

  useEffect(() => {
    active.current = true
    return () => { active.current = false }
  }, [])

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
      <p><button disabled={busy} onClick={() => void run(logout, '')}>Log out</button></p>
    </main>
  )
}
