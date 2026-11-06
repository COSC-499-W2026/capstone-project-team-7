import { useEffect, useRef, useState, type FormEvent } from 'react'
import { createClass, type TeacherClass } from '../api/teacher'
import { SessionEndedError } from '../api/sessionEnded'
import { LANGUAGES } from '../utils/languages'

interface Props {
  disabled: boolean
  onCreated: (classroom: TeacherClass) => void
  onSessionEnded: () => void
}

export default function CreateClassForm({ disabled, onCreated, onSessionEnded }: Props) {
  const [name, setName] = useState('')
  const [language, setLanguage] = useState('fr')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const inFlight = useRef(false)
  const active = useRef(true)

  useEffect(() => {
    active.current = true
    return () => { active.current = false }
  }, [])

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (disabled || inFlight.current || !name.trim()) return
    inFlight.current = true
    setSaving(true)
    setError('')
    try {
      const classroom = await createClass(name, language)
      if (active.current) { setName(''); onCreated(classroom) }
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
    <section aria-label="Create a class">
      <h2>New class</h2>
      <form onSubmit={handleSubmit}>
        <p><label htmlFor="class-name">Class name </label>
          <input id="class-name" value={name} onChange={(e) => setName(e.target.value)} required disabled={disabled || saving} /></p>
        <p><label htmlFor="class-language">Language </label>
          <select id="class-language" value={language} onChange={(e) => setLanguage(e.target.value)} disabled={disabled || saving}>
            {Object.entries(LANGUAGES).map(([code, label]) => <option key={code} value={code}>{label}</option>)}
          </select></p>
        {error && <p role="alert">{error}</p>}
        <button type="submit" disabled={disabled || saving || !name.trim()}>{saving ? 'Creating class...' : 'Create class'}</button>
      </form>
    </section>
  )
}
