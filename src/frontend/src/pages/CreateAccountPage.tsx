import { useState, type FormEvent } from 'react'
import type { LoginResult } from '../api/login'
import { signupAndLogin, type AccountType, type SignupInfo } from '../api/signup'

interface Props {
  onCreated: (login: LoginResult | null) => void
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

// Teachers don't have a student number.
export function signupFields(accountType: AccountType) {
  return accountType === 'teacher' ? FIELDS.filter((field) => field.name !== 'student_number') : FIELDS
}

export default function CreateAccountPage({ onCreated, onBack }: Props) {
  const [accountType, setAccountType] = useState<AccountType>('student')
  const [info, setInfo] = useState<SignupInfo>(EMPTY)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault() // stop the browser from reloading the page
    setError('')
    setLoading(true)
    try {
      onCreated(await signupAndLogin(info, accountType))
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
        <fieldset>
          <legend>I'm a...</legend>
          {(['student', 'teacher'] as const).map((type) => (
            <label key={type}>
              <input
                type="radio"
                name="account_type"
                value={type}
                checked={accountType === type}
                onChange={() => setAccountType(type)}
              />
              {type === 'student' ? "I'm a student" : "I'm a teacher"}
            </label>
          ))}
        </fieldset>
        {accountType === 'teacher' && <p>Your email must be approved by an admin before you can create a teacher account.</p>}
        {signupFields(accountType).map(({ name, label, type }) => (
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
