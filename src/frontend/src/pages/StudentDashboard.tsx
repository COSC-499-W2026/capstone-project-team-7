import { useState } from 'react'
import { startGame, type StartGameResult } from '../api/game'
import { logout } from '../api/logout'

interface Props {
  onGameStarted: (game: StartGameResult) => void
  onLogout: () => void
}

// Buttons for features we haven't built yet. They show but can't be clicked.
const COMING_SOON = ['Choose language', 'Choose difficulty', 'Join a class', 'My progress', 'Badges', 'Leaderboard']

export default function StudentDashboard({ onGameStarted, onLogout }: Props) {
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function run(action: () => Promise<void>) {
    setError('')
    setBusy(true)
    try {
      await action()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main>
      <h1>Student dashboard</h1>

      <button onClick={() => run(async () => onGameStarted(await startGame()))} disabled={busy}>
        Start game
      </button>
      {error && <p role="alert">{error}</p>}

      <h2>Coming soon</h2>
      {COMING_SOON.map((label) => (
        <p key={label}>
          <button disabled>{label}</button>
        </p>
      ))}

      <p>
        <button onClick={() => run(async () => { await logout(); onLogout() })} disabled={busy}>
          Log out
        </button>
      </p>
    </main>
  )
}
