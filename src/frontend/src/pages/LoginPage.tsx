import { useState, type FormEvent } from 'react'
import { login, type LoginResult } from '../api/login'

interface Props {
  onLogin: (result: LoginResult) => void
}

export default function LoginPage({ onLogin }: Props) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault() // stop the browser from reloading the page
    setError('')
    setLoading(true)
    try {
      onLogin(await login(email, password))
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main>
      <h1>Log in</h1>
      <form onSubmit={handleSubmit}>
        <p>
          <label htmlFor="email">Email</label>
          <br />
          <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </p>
        <p>
          <label htmlFor="password">Password</label>
          <br />
          <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </p>
        {error && <p role="alert">{error}</p>}
        <button type="submit" disabled={loading}>
          {loading ? 'Logging in...' : 'Log in'}
        </button>
      </form>
    </main>
  )
}