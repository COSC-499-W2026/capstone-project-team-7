import { useState, type FormEvent } from 'react'
import { signup, type SignupInfo } from '../api/signup'

interface Props {
  onCreated: () => void
  onBack: () => void
}

const FIELDS: { name: keyof SignupInfo; label: string; type: string }[] = [
  { name: 'first_name', label: 'First name', type: 'text' },
  { name: 'last_name', label: 'Last name', type: 'text' },
  { name: 'username', label: 'Username', type: 'text' },
  { name: 'student_number', label: 'Student number', type: 'text' },
  { name: 'email', label: 'Email', type: 'email' },
  { name: 'password', label: 'Password', type: 'password' },
]

const EMPTY: SignupInfo = { email: '', password: '', first_name: '', last_name: '', student_number: '', username: '' }

export default function CreateAccountPage({ onCreated, onBack }: Props) {
  const [info, setInfo] = useState<SignupInfo>(EMPTY)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault() // stop the browser from reloading the page
    setError('')
    setLoading(true)
    try {
      await signup(info)
      onCreated()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main>
      <h1>Create account</h1>
      <form onSubmit={handleSubmit}>
        {FIELDS.map(({ name, label, type }) => (
          <p key={name}>
            <label htmlFor={name}>{label}</label>
            <br />
            <input
              id={name}
              type={type}
              value={info[name]}
              onChange={(e) => setInfo({ ...info, [name]: e.target.value })}
              required
            />
          </p>
        ))}
        {error && <p role="alert">{error}</p>}
        <button type="submit" disabled={loading}>
          {loading ? 'Creating account...' : 'Create account'}
        </button>
      </form>
      <p>
        <a href="#" onClick={(e) => { e.preventDefault(); onBack() }}>Back to login</a>
      </p>
    </main>
  )
}
