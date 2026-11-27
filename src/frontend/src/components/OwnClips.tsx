import { useEffect, useRef, useState } from 'react'
import { SessionEndedError } from '../api/sessionEnded'
import { clipAudioUrl, getClips, retireClip, type OwnClip } from '../api/teacherClips'
import { getClassLocations, type ClassLocation } from '../api/teacherLocations'
import { DIFFICULTY_NAMES } from '../utils/difficulties'
import { locationLabel } from './ClueAudioForm'
import OwnClipsForm from './OwnClipsForm'

interface Props { classId: string; disabled: boolean; onSessionEnded: () => void }

// e.g. "COM 316 · Expert · Café clue"
export function clipTitle(clip: OwnClip) {
  return `${locationLabel(clip)} · ${DIFFICULTY_NAMES[clip.difficulty]} · ${clip.label}`
}

export default function OwnClips({ classId, disabled, onSessionEnded }: Props) {
  const [clips, setClips] = useState<OwnClip[] | null>(null)
  const [locations, setLocations] = useState<ClassLocation[]>([])
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [retiring, setRetiring] = useState('')
  const [attempt, setAttempt] = useState(0)
  const active = useRef(true)

  function showError(err: unknown) {
    if (err instanceof SessionEndedError) onSessionEnded()
    else setError((err as Error).message)
  }

  useEffect(() => {
    let current = true
    active.current = true
    setClips(null)
    setError('')
    Promise.all([getClips(classId), getClassLocations(classId)]).then(([ownClips, items]) => {
      if (current) { setClips(ownClips); setLocations(items) }
    }).catch((err) => { if (current) showError(err) })
    return () => { current = false; active.current = false }
  }, [classId, onSessionEnded, attempt])

  async function handleRetire(clip: OwnClip) {
    if (disabled || retiring) return
    setRetiring(clip.id)
    setError('')
    setMessage('')
    try {
      await retireClip(classId, clip.id)
      if (!active.current) return
      setClips((items) => items?.filter((item) => item.id !== clip.id) ?? null)
      setMessage(`Retired "${clip.label}". Hunts that chose it will play the default clip.`)
    } catch (err) { if (active.current) showError(err) }
    finally { if (active.current) setRetiring('') }
  }

  return (
    <section aria-label="My clips">
      <h2>My clips</h2>
      <p>Your clips are private to you and only play in hunts where you choose them. They don't replace the default clip.</p>
      {error && <p role="alert">{error} {clips === null && <button disabled={disabled} onClick={() => setAttempt(attempt + 1)}>Reload clips</button>}</p>}
      {message && <p role="status">{message}</p>}
      {clips === null ? !error && <p role="status">Loading your clips...</p>
        : clips.length === 0 ? <p>You haven't added any clips in this language yet.</p>
        : <ul>{clips.map((clip) => (
          <li key={clip.id}>
            {clipTitle(clip)}{clip.description && <> · {clip.description}</>}
            {' '}<audio controls preload="none" src={clipAudioUrl(classId, clip.id)} aria-label={`Play ${clip.label}`} />
            {' '}<button disabled={disabled || !!retiring} onClick={() => handleRetire(clip)}>
              {retiring === clip.id ? 'Retiring...' : 'Retire'}</button>
          </li>))}</ul>}
      {clips !== null && <OwnClipsForm classId={classId} locations={locations} disabled={disabled} onSessionEnded={onSessionEnded}
        onAdded={(clip) => { setMessage(''); setClips((items) => [clip, ...(items ?? [])]) }} />}
    </section>
  )
}
