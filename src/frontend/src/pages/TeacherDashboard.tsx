import { useEffect, useState } from 'react'
import { getTeacherClasses, type TeacherClass } from '../api/teacher'
import { logout } from '../api/logout'
import { SessionEndedError } from '../api/sessionEnded'
import ClassRoster from './ClassRoster'

export default function TeacherDashboard({ onLogout }: { onLogout: () => void }) {
  const [classes, setClasses] = useState<TeacherClass[]>([])
  const [selectedId, setSelectedId] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [loggingOut, setLoggingOut] = useState(false)
  const [attempt, setAttempt] = useState(0)
  const selected = classes.find((classroom) => classroom.id === selectedId)
  const languages: Record<string, string> = { fr: 'Français', es: 'Español', de: 'Deutsch', zh: '中文', ja: '日本語', ko: '한국어' }

  useEffect(() => {
    let active = true
    setLoading(true)
    setError('')
    getTeacherClasses().then((items) => {
      if (!active) return
      setClasses(items)
      setSelectedId(items[0]?.id ?? '')
    }).catch((err) => {
      if (!active) return
      if (err instanceof SessionEndedError) onLogout()
      else setError(err instanceof TypeError ? 'Could not load classes, please try again' : (err as Error).message)
    }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [attempt, onLogout])

  async function handleLogout() {
    setLoggingOut(true)
    setError('')
    try {
      await logout()
      onLogout()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoggingOut(false)
    }
  }

  return (
    <div className="teacher-dashboard">
      <aside className="teacher-sidebar">
        <div className="teacher-brand"><span aria-hidden="true">◎</span><strong>Lost In<br />Translation</strong></div>
        <nav aria-label="Teacher navigation">
          <a href="#teacher-classes" aria-current="page">My classes</a>
          <button disabled>Leaderboards</button><button disabled>Profile</button>
          <button onClick={handleLogout} disabled={loggingOut}>{loggingOut ? 'Logging out…' : 'Log out'}</button>
        </nav>
      </aside>
      <main id="teacher-classes">
        <header className="teacher-heading">
          <div><p className="teacher-kicker">Bonjour, teacher</p><h1>{selected?.name ?? 'Teacher dashboard'}</h1>
            {selected && <p className="teacher-tags"><span>{languages[selected.language_code] ?? selected.language_code.toUpperCase()}</span><strong>Code: {selected.class_code}</strong></p>}
          </div>
          <div className="teacher-actions"><button disabled>+ New class</button><button disabled>+ Add student</button></div>
        </header>
        {error && <p role="alert">{error} <button onClick={() => setAttempt(attempt + 1)}>Reload classes</button></p>}
        {loading ? <p role="status">Loading classes…</p> : !error && (
          classes.length === 0 ? <p>No classes assigned yet.</p> : <>
            <label htmlFor="teacher-class">Select a class</label>
            <select id="teacher-class" value={selectedId} onChange={(event) => setSelectedId(event.target.value)}>
              {classes.map((classroom) => <option key={classroom.id} value={classroom.id}>{classroom.name}</option>)}
            </select>
            <div className="teacher-stats" aria-label="Class statistics coming soon">
              {['Students', 'Hunts this week', 'Average score', 'Class finds hardest'].map((label) => <section key={label}><h2>{label}</h2><strong>—</strong><small>Coming soon</small></section>)}
            </div>
            <div className="teacher-panels">
              {selected && <ClassRoster key={selected.id} classId={selected.id} onSessionEnded={onLogout} />}
              <section className="teacher-support"><h2>Could use a hand</h2><p>Class reports coming soon.</p></section>
            </div>
          </>
        )}
      </main>
    </div>
  )
}
