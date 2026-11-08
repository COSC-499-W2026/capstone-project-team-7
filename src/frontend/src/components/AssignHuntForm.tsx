import { useEffect, useRef, useState, type FormEvent } from 'react'
import { assignHunt } from '../api/assignHunt'
import { SessionEndedError } from '../api/sessionEnded'

interface Props {
  classId: string
  disabled: boolean
  onSessionEnded: () => void
}

const DIFFICULTIES = [['basic', 'Basic'], ['advanced', 'Advanced'], ['expert', 'Expert']]

export default function AssignHuntForm({ classId, disabled, onSessionEnded }: Props) {
  const [difficulty, setDifficulty] = useState('basic')
  const [dueDate, setDueDate] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const inFlight = useRef(false)
  const active = useRef(true)
  // Today as "YYYY-MM-DD" in the teacher's own time zone, so the date picker can't pick a past day.
  const today = new Date().toLocaleDateString('en-CA')

  useEffect(() => {
    active.current = true
    return () => { active.current = false }
  }, [])

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (disabled || inFlight.current) return
    inFlight.current = true
    setSaving(true)
    setError('')
    setMessage('')
    try {
      await assignHunt(classId, difficulty, dueDate)
      if (active.current) { setDifficulty('basic'); setDueDate(''); setMessage('Hunt assigned!') }
    } catch (err) {
      if (!active.current) return
      if (err instanceof SessionEndedError) onSessionEnded()
      else setError((err as Error).message)
    } finally {
      inFlight.current = false
      if (active.current) setSaving(false)
    }
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
    </section>
  )
}
