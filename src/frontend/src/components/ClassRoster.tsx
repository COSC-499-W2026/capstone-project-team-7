import { useEffect, useRef, useState, type FormEvent } from 'react'
import { addStudent, getClassRoster, removeStudent, type RosterStudent } from '../api/teacher'
import { SessionEndedError } from '../api/sessionEnded'
import RemovedStudents from './RemovedStudents'

interface Props { classId: string; disabled: boolean; onSessionEnded: () => void }

export default function ClassRoster({ classId, disabled, onSessionEnded }: Props) {
  const [students, setStudents] = useState<RosterStudent[] | null>(null)
  const [number, setNumber] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [attempt, setAttempt] = useState(0)
  const active = useRef(true)
  const inFlight = useRef(false)
  const enrolled = students?.filter((student) => student.status === 'enrolled') ?? []
  const removed = students?.filter((student) => student.status === 'unenrolled') ?? []

  function showError(err: unknown) {
    if (err instanceof SessionEndedError) onSessionEnded()
    else setError((err as Error).message)
  }

  useEffect(() => {
    let current = true
    active.current = true
    setStudents(null)
    setError('')
    getClassRoster(classId).then((items) => { if (current) setStudents(items) })
      .catch((err) => { if (current) showError(err) })
    return () => { current = false; active.current = false }
  }, [classId, onSessionEnded, attempt])

  async function run(action: () => Promise<void>, clearNumber = false) {
    if (disabled || inFlight.current) return
    inFlight.current = true
    setBusy(true)
    setError('')
    try {
      await action()
      if (active.current) {
        if (clearNumber) setNumber('')
        setStudents(null)
        setAttempt((value) => value + 1)
      }
    } catch (err) { if (active.current) showError(err) }
    finally { inFlight.current = false; if (active.current) setBusy(false) }
  }

  function handleAdd(event: FormEvent) {
    event.preventDefault()
    if (students !== null && number.trim()) void run(() => addStudent(classId, number), true)
  }

  function handleRemove(student: RosterStudent) {
    if (disabled || inFlight.current) return
    if (window.confirm(`Remove ${student.first_name} ${student.last_name} from this class? Their account will be kept.`)) {
      void run(() => removeStudent(classId, student.student_id))
    }
  }

  return (
    <section aria-label="Class roster">
      <h2>Class roster</h2>
      {error && <p role="alert">{error} {students === null && <button disabled={disabled || busy} onClick={() => setAttempt(attempt + 1)}>Reload students</button>}</p>}
      {students === null ? !error && <p role="status">Loading students...</p> : enrolled.length === 0 ? <p>No students enrolled yet.</p> : <ul>
        {enrolled.map((student) => <li key={student.student_id}>
          {student.first_name} {student.last_name} · {student.student_number}{' '}
          <button disabled={disabled || busy} aria-label={`Remove ${student.first_name} ${student.last_name} from class`} onClick={() => handleRemove(student)}>Remove</button>
        </li>)}
      </ul>}
      {removed.length > 0 && <RemovedStudents students={removed} />}
      <form onSubmit={handleAdd}>
        <p><label htmlFor="student-number">Student number </label><input id="student-number" value={number} onChange={(e) => setNumber(e.target.value)} required maxLength={30} disabled={disabled || busy || students === null} /></p>
        <button type="submit" disabled={disabled || busy || students === null || !number.trim()}>Add student</button>
      </form>
      <p>Add a registered student by their student number. Removing them keeps their account and class history.</p>
    </section>
  )
}
