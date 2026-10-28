import { useCallback, useEffect, useRef, useState } from 'react'
import { submitAnswer } from './api/answer'
import type { Clue } from './api/clue'
import { getCurrentUser } from './api/currentUser'
import type { StartGameResult } from './api/game'
import { SessionEndedError } from './api/sessionEnded'
import FinishedScreen from './pages/FinishedScreen'
import GameScreen from './pages/GameScreen'
import CreateAccountPage from './pages/CreateAccountPage'
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
  const [sending, setSending] = useState(false)
  const inFlight = useRef(false)
  const [totalPoints, setTotalPoints] = useState(0)
  const [creatingAccount, setCreatingAccount] = useState(false)
  const [loginNotice, setLoginNotice] = useState('')

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
    setNotice('')
    setFinished(false)
    setTotalPoints(0)
    setRole(null)
  }, [])

  function backToDashboard() {
    setGame(null)
    setPhotoFor(null)
    setNotice('')
    setFinished(false)
    setTotalPoints(0)
  }

  async function handlePhoto(photo: File) {
    if (!game || inFlight.current) return
    inFlight.current = true
    setNotice('')
    setSending(true)
    try {
      const result = await submitAnswer(game.game_id, photo)
      setTotalPoints(result.total_points)
      setNotice(`${result.message} ${result.points_awarded} points awarded. Total: ${result.total_points} points.`)
      if (result.finished) setFinished(true)
      if (result.correct) setPhotoFor(null)
    } catch (err) {
      if (err instanceof SessionEndedError) sessionEnded()
      else setNotice((err as Error).message)
    } finally {
      inFlight.current = false
      setSending(false)
    }
  }

  if (checkingLogin) {
    return <main><p>Loading...</p></main>
  }

  if (!role && creatingAccount) {
    return (
      <CreateAccountPage
        onCreated={(login) => {
          setCreatingAccount(false)
          if (login) setRole(login.role)
          else setLoginNotice('Account created! Please log in.')
        }}
        onBack={() => setCreatingAccount(false)}
      />
    )
  }

  if (!role) {
    return (
      <LoginPage
        notice={loginNotice}
        onLogin={(result) => { setLoginNotice(''); setRole(result.role) }}
        onCreateAccount={() => { setLoginNotice(''); setCreatingAccount(true) }}
      />
    )
  }

  if (game && finished) {
    return <FinishedScreen totalSpots={game.total_locations} totalPoints={totalPoints} onBack={backToDashboard} />
  }

  if (game && photoFor) {
    return (
      <PhotoSubmitPage
        spotNumber={photoFor.position}
        totalSpots={photoFor.total_locations}
        sending={sending}
        notice={notice}
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
