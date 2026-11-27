import { useEffect, useRef, useState, type FormEvent } from 'react'
import { SessionEndedError } from '../api/sessionEnded'
import { addClip, type OwnClip } from '../api/teacherClips'
import type { ClassLocation } from '../api/teacherLocations'
import { DIFFICULTIES, DIFFICULTY_NAMES, type Difficulty } from '../utils/difficulties'
import { locationLabel } from './ClueAudioForm'

interface Props {
  classId: string
  locations: ClassLocation[]
  disabled: boolean
  onAdded: (clip: OwnClip) => void
  onSessionEnded: () => void
}

export default function OwnClipsForm({ classId, locations, disabled, onAdded, onSessionEnded }: Props) {
  const [locationId, setLocationId] = useState(locations[0]?.id ?? '')
  const [difficulty, setDifficulty] = useState<Difficulty>('basic')
  const [label, setLabel] = useState('')
  const [description, setDescription] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const active = useRef(true)
  const inFlight = useRef(false)

  useEffect(() => () => { active.current = false }, [])

  function changed() { setMessage(''); setError('') }

  async function handleAdd(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (disabled || inFlight.current || !locationId || !label.trim() || !file) return
    const form = event.currentTarget
    inFlight.current = true
    setBusy(true)
    changed()
    try {
      const saved = await addClip(classId, locationId, file, { difficulty, label, description })
      if (!active.current) return
      onAdded(saved)
      setLabel('')
      setDescription('')
      setFile(null)
      form.reset()
      setMessage(`${DIFFICULTY_NAMES[saved.difficulty]} clip "${saved.label}" added for ${locationLabel(saved)}.`)
    } catch (err) {
      if (!active.current) return
      if (err instanceof SessionEndedError) onSessionEnded()
      else setError((err as Error).message)
    } finally { inFlight.current = false; if (active.current) setBusy(false) }
  }

  const locked = disabled || busy || !locations.length
  return (
    <form onSubmit={handleAdd} aria-label="Add another clip">
      <h3>Add another clip</h3>
      <p><label htmlFor="own-clip-location">Location </label>
        <select id="own-clip-location" value={locationId} onChange={(e) => { setLocationId(e.target.value); changed() }} disabled={locked}>
          {locations.map((item) => <option key={item.id} value={item.id}>{locationLabel(item)}</option>)}
        </select></p>
      <p><label htmlFor="own-clip-difficulty">Difficulty </label>
        <select id="own-clip-difficulty" value={difficulty} onChange={(e) => { setDifficulty(e.target.value as Difficulty); changed() }} disabled={locked}>
          {DIFFICULTIES.map(([value, name]) => <option key={value} value={value}>{name}</option>)}
        </select></p>
      <p><label htmlFor="own-clip-label">Label </label>
        <input id="own-clip-label" value={label} maxLength={60} required disabled={locked}
          onChange={(e) => { setLabel(e.target.value); changed() }} /></p>
      <p><label htmlFor="own-clip-description">Description (optional) </label>
        <textarea id="own-clip-description" value={description} maxLength={300} disabled={locked}
          onChange={(e) => { setDescription(e.target.value); changed() }} /></p>
      <p><label htmlFor="own-clip-file">MP3 file </label>
        <input id="own-clip-file" type="file" accept="audio/mpeg,.mp3" required disabled={locked}
          onChange={(e) => { setFile(e.target.files?.[0] ?? null); changed() }} /></p>
      {error && <p role="alert">{error}</p>}
      {message && <p role="status">{message}</p>}
      <button type="submit" disabled={locked || !label.trim() || !file}>{busy ? 'Adding clip...' : 'Add clip'}</button>
    </form>
  )
}
