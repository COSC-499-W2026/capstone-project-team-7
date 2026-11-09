import { useEffect, useState } from 'react'
import { getLeaderboard, type LeaderboardEntry } from '../api/leaderboard'
import { getProfile, type StudentClass } from '../api/profile'
import { SessionEndedError } from '../api/sessionEnded'
import LeaderboardTable from '../components/LeaderboardTable'
import { languageName } from '../utils/languageName'

interface Props { onBack: () => void; onSessionEnded: () => void }

export default function LeaderboardPage({ onBack, onSessionEnded }: Props) {
  const [classes, setClasses] = useState<StudentClass[] | null>(null)
  const [selected, setSelected] = useState('')
  const [loaded, setLoaded] = useState<{ classroom: StudentClass; entries: LeaderboardEntry[] } | null>(null)
  const [busy, setBusy] = useState(true)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let current = true
    setBusy(true)
    setError('')
    async function load() {
      const options = classes ?? (await getProfile()).classes
      if (!current) return
      setClasses(options)
      const classroom = options.find((item) => item.id === selected) ?? options[0]
      if (!classroom) return
      const entries = await getLeaderboard(classroom.id)
      if (current) setLoaded({ classroom, entries })
    }
    load().catch((err) => {
      if (!current) return
      if (err instanceof SessionEndedError) onSessionEnded()
      else setError((err as Error).message)
    }).finally(() => { if (current) setBusy(false) })
    return () => { current = false }
  }, [selected, attempt, onSessionEnded])

  return (
    <main className="leaderboard">
      <h1>Class leaderboard</h1>
      <button onClick={onBack}>Back</button>
      {classes && classes.length > 0 && <p><label>Class{' '}
        <select value={selected || classes[0].id} disabled={busy} onChange={(e) => setSelected(e.target.value)}>
          {classes.map((item) => <option key={item.id} value={item.id}>{item.name} ({languageName(item.language_code)})</option>)}
        </select>
      </label></p>}
      {busy && <p role="status">Loading leaderboard...</p>}
      {error && <p role="alert">{error} <button disabled={busy} onClick={() => setAttempt(attempt + 1)}>Retry</button></p>}
      {classes?.length === 0 && <p>Join a class from your dashboard to see its leaderboard.</p>}
      {loaded && <LeaderboardTable {...loaded} />}
      <p>Points count completed games in the class language. Equal scores share a rank.</p>
    </main>
  )
}
