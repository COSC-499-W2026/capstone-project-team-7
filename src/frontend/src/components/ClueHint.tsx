import { useEffect, useState } from 'react'
import { captureLocation } from '../api/location'
import { apiRequest } from '../api/request'
import { SessionEndedError } from '../api/sessionEnded'
import type { Clue } from '../api/clue'

interface Props {
  gameId: string
  clue: Clue
  onSessionEnded: () => void
}

export default function ClueHint({ gameId, clue, onSessionEnded }: Props) {
  const [ready, setReady] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [retry, setRetry] = useState(0)

  useEffect(() => {
    const timer = window.setTimeout(() => setReady(true), Math.max(0, 300 - clue.clue_elapsed_seconds) * 1000)
    return () => window.clearTimeout(timer)
  }, [clue.clue_elapsed_seconds])

  useEffect(() => {
    if (!ready) return
    let cancelled = false
    async function loadHint() {
      setLoading(true)
      setError('')
      try {
        const reading = await captureLocation()
        reading.set('position', String(clue.position))
        reading.set('revision', String(clue.revision ?? 0))
        const res = await apiRequest(`/api/game/${encodeURIComponent(gameId)}/clue/hint?${reading}`, undefined,
          { fallback: 'Could not get a hint. Please try again.', useDetail: true })
        const body = await res.json() as { message: string }
        if (!cancelled) setMessage(body.message)
      } catch (err) {
        if (!cancelled) {
          if (err instanceof SessionEndedError) onSessionEnded()
          else setError((err as Error).message)
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void loadHint()
    return () => { cancelled = true }
  }, [ready, gameId, clue.position, clue.revision, onSessionEnded, retry])

  if (!ready) return null
  return <section aria-label="Hint" aria-live="polite">
    {loading && <p>Checking your location for a hint...</p>}
    {message && <p>Hint: {message}</p>}
    {error && <><p>{error}</p><button onClick={() => setRetry(retry + 1)}>Try hint again</button></>}
  </section>
}
