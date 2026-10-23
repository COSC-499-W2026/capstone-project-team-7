import { useState } from 'react'
import LoginPage from './pages/LoginPage'

export default function App() {
  const [role, setRole] = useState<string | null>(null)

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