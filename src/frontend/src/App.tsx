import { useEffect, useState } from 'react'
import CreateAccountPage from './CreateAccountPage'
import LoadingScreen from './LoadingScreen'
import LoginPage from './LoginPage'

type Page = 'loading' | 'login' | 'createAccount'

export default function App() {
  const [page, setPage] = useState<Page>('loading')
  const [progress, setProgress] = useState(0)

  // Fill the loading bar step by step, then switch to the login page shortly after it is full
  useEffect(() => {
    if (page !== 'loading') return
    if (progress < 100) {
      const step = setTimeout(() => setProgress(progress + 10), 150)
      return () => clearTimeout(step)
    }
    const done = setTimeout(() => setPage('login'), 400)
    return () => clearTimeout(done)
  }, [page, progress])

  if (page === 'loading') {
    return <LoadingScreen progress={progress} />
  }

  if (page === 'createAccount') {
    return <CreateAccountPage onBackToLogin={() => setPage('login')} />
  }

  // Guest play gets its own page in a later PR
  return <LoginPage onCreateAccount={() => setPage('createAccount')} onPlayAsGuest={() => {}} />
}
