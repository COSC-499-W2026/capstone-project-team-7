import { useState } from 'react'
import type { FormEvent } from 'react'
import './LoginPage.css'

interface LoginPageProps {
  onCreateAccount: () => void
  onPlayAsGuest: () => void
}

export default function LoginPage({ onCreateAccount, onPlayAsGuest }: LoginPageProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  function handleSubmit(event: FormEvent) {
    event.preventDefault() // stops the browser from reloading the page
  }

  return (
    <main className="screen login-page">
      <header className="login-header">
        <div className="login-logo">
          <img src="/icons/logo.svg" alt="" width={48} height={48} />
        </div>
        <h1>Welcome, explorer!</h1>
        <p className="subtitle">Log in to keep your points and badges.</p>
      </header>

      <form className="login-form" onSubmit={handleSubmit}>
        <label className="field">
          Email
          <input
            className="text-input"
            type="email"
            autoComplete="email"
            placeholder="you@student.ubc.ca"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </label>
        <label className="field">
          Password
          <input
            className="text-input"
            type="password"
            autoComplete="current-password"
            placeholder="Your password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>
        <a href="#" className="forgot-link">Forgot password?</a>

        <button className="game-button" type="submit">Login</button>
      </form>

      <div className="login-divider"><span>or</span></div>

      <button className="game-button game-button--white" type="button" onClick={onCreateAccount}>
        Create account
      </button>
      <button className="game-button game-button--yellow" type="button" onClick={onPlayAsGuest}>
        Play as guest
      </button>
      <p className="subtitle login-note">Guests can play, but points and badges won't be saved.</p>
    </main>
  )
}
