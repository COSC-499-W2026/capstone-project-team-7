import { useEffect, useState } from 'react'
import { startGame, type StartGameResult } from '../api/game'
import { logout } from '../api/logout'
import { getOngoingGames, type OngoingGame } from '../api/ongoingGames'
import { SessionEndedError } from '../api/sessionEnded'
import OngoingGames from '../components/OngoingGames'

interface Props {
  onOpenGame: (game: StartGameResult) => void
  onLogout: () => void
}

// Buttons for features we haven't built yet. They show but can't be clicked.
const COMING_SOON = ['Choose language', 'Choose difficulty', 'Join a class', 'My progress', 'Badges', 'Leaderboard']

export default function StudentDashboard({ onOpenGame, onLogout }: Props) {
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [games, setGames] = useState<OngoingGame[]>([])

  // Load once when the dashboard opens; it opens again after every game, so the list stays current.
  useEffect(() => {
    getOngoingGames()
      .then(setGames)
      .catch((err) => {
        if (err instanceof SessionEndedError) onLogout()
        else setError((err as Error).message)
      })
  }, [])

  async function run(action: () => Promise<void>) {
    setError('')
    setBusy(true)
    try {
      await action()
    } catch (err) {
      if (err instanceof SessionEndedError) onLogout()
      else setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main>
      <h1>Student dashboard</h1>

      <button onClick={() => run(async () => onOpenGame(await startGame()))} disabled={busy}>
        Start game
      </button>
      {error && <p role="alert">{error}</p>}

      <OngoingGames games={games} disabled={busy} onResume={onOpenGame} />

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
