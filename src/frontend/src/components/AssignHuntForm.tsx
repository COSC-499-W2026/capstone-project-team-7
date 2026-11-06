import { useEffect, useRef, useState, type FormEvent } from 'react'
import { assignHunt, deleteHunt, getAssignedHunts, hideOverdue, type ClassHunt } from '../api/assignHunt'
import { SessionEndedError } from '../api/sessionEnded'

interface Props {
  classId: string
  disabled: boolean
  onSessionEnded: () => void
}

const DIFFICULTIES = [['basic', 'Basic'], ['advanced', 'Advanced'], ['expert', 'Expert']]
const DIFFICULTY_NAMES: Record<string, string> = Object.fromEntries(DIFFICULTIES)

export default function AssignHuntForm({ classId, disabled, onSessionEnded }: Props) {
  const [difficulty, setDifficulty] = useState('basic')
  const [dueDate, setDueDate] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [hunts, setHunts] = useState<ClassHunt[] | null>(null)
  const [listError, setListError] = useState('')
  const [refresh, setRefresh] = useState(0)
  const [showPastDue, setShowPastDue] = useState(false)
  const [confirmingId, setConfirmingId] = useState<string | null>(null)
  const inFlight = useRef(false)
  const active = useRef(true)
  // Today as "YYYY-MM-DD" in the teacher's own time zone, so the date picker can't pick a past day.
  const today = new Date().toLocaleDateString('en-CA')
  const shown = hunts && (showPastDue ? hunts : hideOverdue(hunts, today))

  useEffect(() => {
    active.current = true
    return () => { active.current = false }
  }, [])

  useEffect(() => {
    let current = true
    setHunts(null)
    setListError('')
    getAssignedHunts(classId).then((items) => { if (current) setHunts(items) })
      .catch((err) => {
        if (!current) return
        if (err instanceof SessionEndedError) onSessionEnded()
        else setListError((err as Error).message)
      })
    return () => { current = false }
  }, [classId, onSessionEnded, refresh])

  // Runs one change at a time, then shows the done message and reloads the list.
  async function run(action: () => Promise<void>, done: string) {
    if (disabled || inFlight.current) return
    inFlight.current = true
    setSaving(true)
    setError('')
    setMessage('')
    try {
      await action()
      if (active.current) { setMessage(done); setRefresh((n) => n + 1) }
    } catch (err) {
      if (!active.current) return
      if (err instanceof SessionEndedError) onSessionEnded()
      else setError((err as Error).message)
    } finally {
      inFlight.current = false
      if (active.current) setSaving(false)
    }
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    run(async () => {
      await assignHunt(classId, difficulty, dueDate)
      setDifficulty('basic')
      setDueDate('')
    }, 'Hunt assigned!')
  }

  function handleRemove(hunt: ClassHunt) {
    setConfirmingId(null)
    run(() => deleteHunt(classId, hunt.id), 'Hunt removed.')
  }

  return (
    <section aria-label="Assign a hunt">
      <h2>Assign a hunt</h2>
      <form onSubmit={handleSubmit}>
        <p><label htmlFor="hunt-difficulty">Difficulty </label>
          <select id="hunt-difficulty" value={difficulty} onChange={(e) => setDifficulty(e.target.value)} disabled={disabled || saving}>
            {DIFFICULTIES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select></p>
        <p><label htmlFor="hunt-due-date">Due date (optional) </label>
          <input id="hunt-due-date" type="date" min={today} value={dueDate} onChange={(e) => setDueDate(e.target.value)} disabled={disabled || saving} /></p>
        {error && <p role="alert">{error}</p>}
        {message && <p role="status">{message}</p>}
        <button type="submit" disabled={disabled || saving}>{saving ? 'Assigning hunt...' : 'Assign hunt'}</button>
      </form>
      <h3>Currently assigned</h3>
      <p><label><input type="checkbox" checked={showPastDue} onChange={(e) => setShowPastDue(e.target.checked)} /> Show past-due hunts</label></p>
      {listError ? <p role="alert">{listError}</p>
        : shown === null ? <p>Loading hunts...</p>
        : shown.length === 0 ? <p>{hunts?.length ? 'No current hunts.' : 'No hunts assigned yet.'}</p>
        : <ul>{shown.map((hunt) => (
          <li key={hunt.id}>
            {DIFFICULTY_NAMES[hunt.difficulty] ?? hunt.difficulty} · Assigned {new Date(hunt.assigned_at).toLocaleDateString('en-CA')}
            {' · '}{hunt.due_date ? `Due ${hunt.due_date}` : 'No due date'}
            {confirmingId === hunt.id ? <>
              {' '}Remove this hunt? Students in this class will no longer see it.
              {' '}<button type="button" onClick={() => handleRemove(hunt)} disabled={disabled || saving}>Yes, remove</button>
              {' '}<button type="button" onClick={() => setConfirmingId(null)}>Cancel</button>
            </> : <>{' '}<button type="button" onClick={() => setConfirmingId(hunt.id)} disabled={disabled || saving}>Remove</button></>}
          </li>
        ))}</ul>}
    </section>
  )
}
