import { useEffect, useRef, useState } from 'react'
import { getTeacherClasses, type TeacherClass } from '../api/teacher'
import { logout } from '../api/logout'
import { SessionEndedError } from '../api/sessionEnded'
import CreateClassForm from '../components/CreateClassForm'
import ClassRoster from '../components/ClassRoster'
import { languageName } from '../utils/languageName'

export default function TeacherDashboard({ onLogout }: { onLogout: () => void }) {
  const [classes, setClasses] = useState<TeacherClass[] | null>(null)
  const [selectedId, setSelectedId] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [attempt, setAttempt] = useState(0)
  const inFlight = useRef(false)
  const selected = classes?.find((item) => item.id === selectedId)

  useEffect(() => {
    let active = true
    setClasses(null)
    setError('')
    getTeacherClasses().then((items) => {
      if (active) { setClasses(items); setSelectedId(items[0]?.id ?? '') }
    }).catch((err) => {
      if (!active) return
      if (err instanceof SessionEndedError) onLogout()
      else setError((err as Error).message)
    })
    return () => { active = false }
  }, [attempt, onLogout])

  async function handleLogout() {
    if (inFlight.current) return
    inFlight.current = true
    setError('')
    setBusy(true)
    try { await logout(); onLogout() }
    catch (err) {
      if (err instanceof SessionEndedError) onLogout()
      else setError((err as Error).message)
    } finally { inFlight.current = false; setBusy(false) }
  }

  return (
    <main>
      <h1>Teacher dashboard</h1>
      {error && <p role="alert">{error} {classes === null && <button onClick={() => setAttempt(attempt + 1)}>Reload classes</button>}</p>}
      <h2>My classes</h2>
      {classes === null ? !error && <p role="status">Loading classes...</p> : classes.length === 0 ? <p>No classes assigned yet.</p> : <>
        <label htmlFor="teacher-class">Select a class </label>
        <select id="teacher-class" value={selectedId} disabled={busy} onChange={(e) => setSelectedId(e.target.value)}>
          {classes.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
        </select>
        {selected && <p>Language: {languageName(selected.language_code)} · Class code: <strong>{selected.class_code}</strong></p>}
        {selected && <ClassRoster key={selected.id} classId={selected.id} disabled={busy} onSessionEnded={onLogout} />}
      </>}
      <CreateClassForm disabled={busy || classes === null} onSessionEnded={onLogout} onCreated={(classroom) => {
        setClasses((items) => [...(items ?? []), classroom])
        setSelectedId(classroom.id)
      }} />
      <p><button onClick={handleLogout} disabled={busy}>Log out</button></p>
    </main>
  )
}
