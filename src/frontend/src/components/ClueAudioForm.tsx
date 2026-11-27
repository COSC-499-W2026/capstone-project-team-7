import { useEffect, useRef, useState, type FormEvent } from 'react'
import { SessionEndedError } from '../api/sessionEnded'
import { getClassLocations, uploadClueAudio, type ClassLocation } from '../api/teacherLocations'
import { DIFFICULTIES, DIFFICULTY_NAMES, type Difficulty } from '../utils/difficulties'

interface Props { classId: string; disabled: boolean; onSessionEnded: () => void }

export function locationLabel(location: Pick<ClassLocation, 'building' | 'room_number'>) {
  return `${location.building} ${location.room_number}`
}

// e.g. "Has Basic, Expert · Missing Advanced"
export function audioStatus(location: ClassLocation) {
  const has = DIFFICULTIES.filter(([value]) => location.audio[value]).map(([, label]) => label)
  const missing = DIFFICULTIES.filter(([value]) => !location.audio[value]).map(([, label]) => label)
  if (!missing.length) return 'Audio for every level'
  if (!has.length) return 'No audio yet'
  return `Has ${has.join(', ')} · Missing ${missing.join(', ')}`
}

export default function ClueAudioForm({ classId, disabled, onSessionEnded }: Props) {
  const [locations, setLocations] = useState<ClassLocation[] | null>(null)
  const [locationId, setLocationId] = useState('')
  const [difficulty, setDifficulty] = useState<Difficulty>('basic')
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const [attempt, setAttempt] = useState(0)
  const active = useRef(true)
  const inFlight = useRef(false)
  const selected = locations?.find((item) => item.id === locationId)

  function showError(err: unknown) {
    if (err instanceof SessionEndedError) onSessionEnded()
    else setError((err as Error).message)
  }

  useEffect(() => {
    let current = true
    active.current = true
    setLocations(null)
    setError('')
    getClassLocations(classId).then((items) => {
      if (current) { setLocations(items); setLocationId(items[0]?.id ?? '') }
    }).catch((err) => { if (current) showError(err) })
    return () => { current = false; active.current = false }
  }, [classId, onSessionEnded, attempt])

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (disabled || inFlight.current || !selected || !file) return
    const form = event.currentTarget
    inFlight.current = true
    setBusy(true)
    setError('')
    setMessage('')
    try {
      const saved = await uploadClueAudio(classId, selected.id, file, difficulty)
      if (!active.current) return
      setLocations((items) => items?.map((item) => item.id === saved.id ? saved : item) ?? null)
      setFile(null)
      form.reset()
      setMessage(`${DIFFICULTY_NAMES[difficulty]} audio saved for ${locationLabel(saved)}.`)
    } catch (err) { if (active.current) showError(err) }
    finally { inFlight.current = false; if (active.current) setBusy(false) }
  }

  const locked = disabled || busy || !locations?.length
  return (
    <section aria-label="Clue audio">
      <h2>Clue audio</h2>
      {error && <p role="alert">{error} {locations === null && <button disabled={disabled || busy} onClick={() => setAttempt(attempt + 1)}>Reload locations</button>}</p>}
      {message && <p role="status">{message}</p>}
      {locations === null ? !error && <p role="status">Loading locations...</p>
        : locations.length === 0 ? <p>No locations have a clue in this class's language yet.</p>
        : <ul>{locations.map((item) => <li key={item.id}>{locationLabel(item)} · {audioStatus(item)}</li>)}</ul>}
      <form onSubmit={handleUpload}>
        <p><label htmlFor="audio-location">Location </label>
          <select id="audio-location" value={locationId} onChange={(e) => { setLocationId(e.target.value); setMessage('') }} disabled={locked}>
            {locations?.map((item) => <option key={item.id} value={item.id}>{locationLabel(item)}</option>)}
          </select></p>
        <p><label htmlFor="audio-difficulty">Difficulty </label>
          <select id="audio-difficulty" value={difficulty} onChange={(e) => { setDifficulty(e.target.value as Difficulty); setMessage('') }} disabled={locked}>
            {DIFFICULTIES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select></p>
        <p><label htmlFor="audio-file">MP3 file </label>
          <input id="audio-file" type="file" accept="audio/mpeg,.mp3" required disabled={locked}
            onChange={(e) => { setFile(e.target.files?.[0] ?? null); setMessage('') }} /></p>
        <button type="submit" disabled={locked || !file}>{busy ? 'Uploading...' : selected?.audio[difficulty] ? 'Replace audio' : 'Upload audio'}</button>
      </form>
      <p>Clips are shared, so replacing one changes it for every class that uses this location.</p>
    </section>
  )
}
