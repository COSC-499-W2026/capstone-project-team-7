import { useEffect, useState } from 'react'
import { getDebrief, type Debrief } from '../api/debrief'
import { SessionEndedError } from '../api/sessionEnded'
import DebriefView from '../components/DebriefView'

interface Props {
  onBack: () => void
  onSessionEnded: () => void
}

export default function DebriefPage({ onBack, onSessionEnded }: Props) {
  const [data, setData] = useState<Debrief | null>(null)
  const [error, setError] = useState('')
  const [retry, setRetry] = useState(0)
  useEffect(() => {
    let cancelled = false
    setError('')
    getDebrief().then((result) => { if (!cancelled) setData(result) }).catch((err: Error) => {
      if (cancelled) return
      if (err instanceof SessionEndedError) onSessionEnded()
      else setError(err.message)
    })
    return () => { cancelled = true }
  }, [retry, onSessionEnded])
  return <main>
    <h1>Hunt debrief</h1>
    <button onClick={onBack}>Back</button>
    {error && <><p role="alert">{error}</p><button onClick={() => setRetry(retry + 1)}>Try again</button></>}
    {!data && !error && <p>Loading your debrief...</p>}
    {data && <DebriefView debrief={data} />}
  </main>
}
