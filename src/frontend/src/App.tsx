import { useEffect, useState } from 'react'
import { getCurrentUser } from './api/currentUser'
import LoginPage from './pages/LoginPage'

export default function App() {
  const [role, setRole] = useState<string | null>(null)
  const [checkingLogin, setCheckingLogin] = useState(true)

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

  // Placeholder until the game screens exist.
  return (
    <main>
      <h1>Logged in</h1>
      <p>You are logged in as a {role}.</p>
    </main>
  )
}
