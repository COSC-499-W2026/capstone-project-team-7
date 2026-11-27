import { useEffect, useState } from 'react'
import { getClassLeaderboard, type LeaderboardEntry } from '../api/leaderboard'
import { SessionEndedError } from '../api/sessionEnded'
import type { TeacherClass } from '../api/teacher'
import LeaderboardTable from './LeaderboardTable'

interface Props { classroom: TeacherClass; disabled: boolean; onSessionEnded: () => void }

export default function ClassLeaderboard({ classroom, disabled, onSessionEnded }: Props) {
  const [entries, setEntries] = useState<LeaderboardEntry[] | null>(null)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let current = true
    setEntries(null)
    setError('')
    getClassLeaderboard(classroom.id).then((items) => { if (current) setEntries(items) })
      .catch((err) => {
        if (!current) return
        if (err instanceof SessionEndedError) onSessionEnded()
        else setError((err as Error).message)
      })
    return () => { current = false }
  }, [classroom.id, onSessionEnded, attempt])

  return (
    <section aria-label="Class leaderboard">
      <h2>Class leaderboard</h2>
      {error && <p role="alert">{error} <button disabled={disabled} onClick={() => setAttempt(attempt + 1)}>Retry</button></p>}
      {entries === null ? !error && <p role="status">Loading leaderboard...</p> : <LeaderboardTable classroom={classroom} entries={entries} />}
    </section>
  )
}
