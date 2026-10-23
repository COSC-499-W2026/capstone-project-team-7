import { useEffect, useState } from 'react'
import type { Clue } from './api/clue'
import { getCurrentUser } from './api/currentUser'
import type { StartGameResult } from './api/game'
import GameScreen from './pages/GameScreen'
import LoginPage from './pages/LoginPage'
import StudentDashboard from './pages/StudentDashboard'

export default function App() {
  const [role, setRole] = useState<string | null>(null)
  const [checkingLogin, setCheckingLogin] = useState(true)
  const [game, setGame] = useState<StartGameResult | null>(null)
  const [photoFor, setPhotoFor] = useState<Clue | null>(null)

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

  // Placeholder until the photo submission page is connected.
  if (game && photoFor) {
    return (
      <main>
        <h1>Photo for spot {photoFor.position} of {photoFor.total_locations}</h1>
        <p>The camera page will open here.</p>
        <button onClick={() => setPhotoFor(null)}>Back to clue</button>
      </main>
    )
  }

  if (game) {
    return <GameScreen gameId={game.game_id} onSubmitPhoto={setPhotoFor} onBack={() => setGame(null)} />
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
