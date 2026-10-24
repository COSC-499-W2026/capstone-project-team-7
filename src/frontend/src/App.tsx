import { useEffect, useState } from 'react'
import { submitAnswer } from './api/answer'
import type { Clue } from './api/clue'
import { getCurrentUser } from './api/currentUser'
import type { StartGameResult } from './api/game'
import FinishedScreen from './pages/FinishedScreen'
import GameScreen from './pages/GameScreen'
import LoginPage from './pages/LoginPage'
import PhotoSubmitPage from './pages/PhotoSubmitPage'
import StudentDashboard from './pages/StudentDashboard'

export default function App() {
  const [role, setRole] = useState<string | null>(null)
  const [checkingLogin, setCheckingLogin] = useState(true)
  const [game, setGame] = useState<StartGameResult | null>(null)
  const [photoFor, setPhotoFor] = useState<Clue | null>(null)
  const [notice, setNotice] = useState('')
  const [finished, setFinished] = useState(false)

  // On page load, ask the backend if the login cookie is still valid.
  useEffect(() => {
    getCurrentUser()
      .then((user) => setRole(user?.role ?? null))
      .finally(() => setCheckingLogin(false))
  }, [])

  function backToDashboard() {
    setGame(null)
    setPhotoFor(null)
    setNotice('')
    setFinished(false)
  }

  async function handlePhoto(photo: File) {
    if (!game) return
    try {
      const result = await submitAnswer(game.game_id, photo)
      if (result.finished) setFinished(true)
      else setNotice(result.correct ? 'Correct! On to the next spot.' : 'Not quite, try again.')
    } catch (err) {
      setNotice((err as Error).message)
    }
    setPhotoFor(null)
  }

  if (checkingLogin) {
    return <main><p>Loading...</p></main>
  }

  if (!role) {
    return <LoginPage onLogin={(result) => setRole(result.role)} />
  }

  if (game && finished) {
    return <FinishedScreen totalSpots={game.total_locations} onBack={backToDashboard} />
  }

  if (game && photoFor) {
    return (
      <PhotoSubmitPage
        spotNumber={photoFor.position}
        totalSpots={photoFor.total_locations}
        onSubmit={handlePhoto}
        onClose={() => setPhotoFor(null)}
      />
    )
  }

  if (game) {
    return (
      <GameScreen
        gameId={game.game_id}
        notice={notice}
        onSubmitPhoto={(clue) => { setNotice(''); setPhotoFor(clue) }}
        onBack={backToDashboard}
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
