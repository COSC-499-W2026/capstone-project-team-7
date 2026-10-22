import { useEffect, useState } from 'react'
import LoadingScreen from './LoadingScreen'
import LoginPage from './LoginPage'

export default function App() {
  const [progress, setProgress] = useState(0)
  const [showLogin, setShowLogin] = useState(false)

  // Fill the loading bar step by step, then switch to the login page shortly after it is full
  useEffect(() => {
    if (progress < 100) {
      const step = setTimeout(() => setProgress(progress + 10), 150)
      return () => clearTimeout(step)
    }
    const done = setTimeout(() => setShowLogin(true), 400)
    return () => clearTimeout(done)
  }, [progress])

  if (!showLogin) {
    return <LoadingScreen progress={progress} />
  }

  // Create account and guest play get their own pages in later PRs
  return <LoginPage onCreateAccount={() => {}} onPlayAsGuest={() => {}} />
}
