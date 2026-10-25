import { useEffect, useState } from 'react'
import { getCurrentUser } from './api/currentUser'
import type { StartGameResult } from './api/game'
import LoginPage from './pages/LoginPage'
import StudentDashboard from './pages/StudentDashboard'

export default function App() {
  const [role, setRole] = useState<string | null>(null)
  const [checkingLogin, setCheckingLogin] = useState(true)
  const [game, setGame] = useState<StartGameResult | null>(null)

  // On page load, ask the backend if the login cookie is still valid.
  useEffect(() => {
    getCurrentUser()
      .then((user) => setRole(user?.role ?? null))
      .finally(() => setCheckingLogin(false))
  }, [])

  if (checkingLogin) {
    return <main><p>Loading...</p></main>
  }

  if (!role) {
    return <LoginPage onLogin={(result) => setRole(result.role)} />
  }

  // Placeholder until the clue screen exists.
  if (game) {
    return (
      <main>
        <h1>Game started</h1>
        <p>Clue {game.current_position} of {game.total_locations} will show here.</p>
        <button onClick={() => setGame(null)}>Back to dashboard</button>
      </main>
    )
  }

  if (role === 'student') {
    return <StudentDashboard onGameStarted={setGame} onLogout={() => setRole(null)} />
  }

  // Teacher and admin dashboards come later.
  return (
    <main>
      <h1>Logged in</h1>
      <p>You are logged in as a {role}.</p>
    </main>
  )
}
