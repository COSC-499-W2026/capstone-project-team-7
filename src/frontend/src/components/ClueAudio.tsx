import { useEffect, useRef, useState } from 'react'
import { getClueAudio } from '../api/clueAudio'
import { SessionEndedError } from '../api/sessionEnded'

interface Props {
  url: string
  remaining: number | null
  onSessionEnded: () => void
}

export default function ClueAudio({ url, remaining, onSessionEnded }: Props) {
  const [playsLeft, setPlaysLeft] = useState(remaining)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const inFlight = useRef(false)
  const player = useRef<HTMLAudioElement | null>(null)
  const source = useRef<string | null>(null)
  const active = useRef(true)

  function releaseAudio() {
    player.current?.pause()
    player.current = null
    if (source.current) URL.revokeObjectURL(source.current)
    source.current = null
  }

  useEffect(() => {
    active.current = true
    return () => { active.current = false; releaseAudio() }
  }, [])

  async function play() {
    if (inFlight.current || playsLeft === 0) return
    inFlight.current = true
    setBusy(true)
    setError('')
    try {
      const result = await getClueAudio(url)
      if (!active.current) return
      setPlaysLeft(result.remaining)
      source.current = URL.createObjectURL(result.audio)
      const audio = new Audio(source.current)
      player.current = audio
      audio.onended = () => { releaseAudio(); inFlight.current = false; setBusy(false) }
      audio.onerror = () => {
        releaseAudio()
        inFlight.current = false
        setBusy(false)
        setError('Audio could not play. Please try again.')
      }
      await audio.play()
    } catch (err) {
      releaseAudio()
      inFlight.current = false
      if (!active.current) return
      setBusy(false)
      if (err instanceof SessionEndedError) onSessionEnded()
      else {
        const message = err instanceof Error ? err.message : 'Audio could not play. Please try again.'
        if (message === 'No audio plays remaining for this clue') setPlaysLeft(0)
        setError(message)
      }
    }
  }

  return (
    <div>
      <p role="status">{playsLeft === null ? 'Unlimited audio plays' : `${playsLeft} audio plays remaining`}</p>
      <button onClick={play} disabled={busy || playsLeft === 0}>
        {busy ? 'Playing audio...' : 'Play clue'}
      </button>
      {playsLeft === 0 && <p>No audio plays remaining for this clue.</p>}
      {error && <p role="alert">{error}</p>}
    </div>
  )
}
