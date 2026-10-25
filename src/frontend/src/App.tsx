import { useCallback, useEffect, useState } from 'react'
import type { Clue } from './api/clue'
import { getCurrentUser } from './api/currentUser'
import type { StartGameResult } from './api/game'
import GameScreen from './pages/GameScreen'
import LoginPage from './pages/LoginPage'
import PhotoSubmitPage from './pages/PhotoSubmitPage'
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

  // The login session ended mid-game, so drop the game and show the login page.
  // useCallback keeps it the same function, so GameScreen doesn't reload the clue on every render.
  const sessionEnded = useCallback(() => {
    setGame(null)
    setPhotoFor(null)
    setRole(null)
  }, [])

  if (checkingLogin) {
    return <main><p>Loading...</p></main>
  }

  if (!role) {
    return <LoginPage onLogin={(result) => setRole(result.role)} />
  }

  // The photo isn't sent anywhere yet; submitting answers comes in the next PR.
  if (game && photoFor) {
    return (
      <PhotoSubmitPage
        spotNumber={photoFor.position}
        totalSpots={photoFor.total_locations}
        onSubmit={() => setPhotoFor(null)}
        onClose={() => setPhotoFor(null)}
      />
    )
  }

  if (game) {
    return (
      <GameScreen
        gameId={game.game_id}
        onSubmitPhoto={setPhotoFor}
        onBack={() => setGame(null)}
        onSessionEnded={sessionEnded}
      />
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
