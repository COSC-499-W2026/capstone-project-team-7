import { useState } from 'react'
import type { FormEvent } from 'react'
import './CreateAccountPage.css'

export const MIN_PASSWORD_LENGTH = 8

// Returns what is wrong with the password, or an empty string if it is fine
export function passwordProblem(password: string, confirmPassword: string) {
  if (password.length < MIN_PASSWORD_LENGTH) return `Your password needs at least ${MIN_PASSWORD_LENGTH} characters.`
  if (password !== confirmPassword) return "Your passwords don't match."
  return ''
}

interface CreateAccountPageProps {
  onBackToLogin: () => void
}

export default function CreateAccountPage({ onBackToLogin }: CreateAccountPageProps) {
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [studentNumber, setStudentNumber] = useState('')
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')

  function handleSubmit(event: FormEvent) {
    event.preventDefault() // stops the browser from reloading the page
    setError(passwordProblem(password, confirmPassword))
  }

  return (
    <main className="screen">
      <header className="signup-header">
        <button className="signup-back" type="button" aria-label="Back to login" onClick={onBackToLogin}>
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M15 5l-7 7 7 7" />
          </svg>
        </button>
        <div>
          <h1>Join the hunt!</h1>
          <p className="subtitle">Make an account to save your points and badges.</p>
        </div>
      </header>

      <form className="signup-form" onSubmit={handleSubmit}>
        <div className="signup-row">
          <label className="field">
            First name
            <input className="text-input" autoComplete="given-name" value={firstName}
              onChange={(event) => setFirstName(event.target.value)} required />
          </label>
          <label className="field">
            Last name
            <input className="text-input" autoComplete="family-name" value={lastName}
              onChange={(event) => setLastName(event.target.value)} required />
          </label>
        </div>
        <label className="field">
          Student number
          <input className="text-input" inputMode="numeric" maxLength={30} value={studentNumber}
            onChange={(event) => setStudentNumber(event.target.value)} required />
        </label>
        <label className="field">
          Username
          <input className="text-input" autoComplete="username" maxLength={50} value={username}
            onChange={(event) => setUsername(event.target.value)} required />
        </label>
        <label className="field">
          Email
          <input className="text-input" type="email" autoComplete="email" placeholder="you@student.ubc.ca"
            value={email} onChange={(event) => setEmail(event.target.value)} required />
        </label>
        <label className="field">
          Password
          <input className="text-input" type="password" autoComplete="new-password" value={password}
            onChange={(event) => setPassword(event.target.value)} required />
          <span className="signup-hint">At least {MIN_PASSWORD_LENGTH} characters</span>
        </label>
        <label className="field">
          Confirm password
          <input className="text-input" type="password" autoComplete="new-password" value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)} required />
        </label>

        {error && <p className="error-message" role="alert">{error}</p>}

        <button className="game-button" type="submit">Create account</button>
      </form>

      <p className="signup-login">
        Already have an account?{' '}
        <button className="signup-link" type="button" onClick={onBackToLogin}>Log in</button>
      </p>
    </main>
  )
}
