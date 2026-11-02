import { useState, type FormEvent } from 'react'
import { joinClass } from '../api/joinClass'
import { SessionEndedError } from '../api/sessionEnded'

interface Props {
  onSessionEnded: () => void
}

export function joinedMessage(className: string) {
  return `You joined ${className}.`
}

export default function JoinClass({ onSessionEnded }: Props) {
  const [code, setCode] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const [joined, setJoined] = useState('')

  async function handleSubmit(event: FormEvent) {
    event.preventDefault() // stop the browser from reloading the page
    setError('')
    setJoined('')
    setSending(true)
    try {
      const classroom = await joinClass(code)
      setJoined(classroom.name)
      setCode('')
    } catch (err) {
      if (err instanceof SessionEndedError) onSessionEnded()
      else setError((err as Error).message)
    } finally {
      setSending(false)
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <h2>Join a class</h2>
      <label htmlFor="class-code">Class code</label>{' '}
      <input id="class-code" value={code} maxLength={12} onChange={(e) => setCode(e.target.value)} />{' '}
      <button type="submit" disabled={sending || !code.trim()}>
        {sending ? 'Joining...' : 'Join'}
      </button>
      {error && <p role="alert">{error}</p>}
      {joined && <p>{joinedMessage(joined)}</p>}
    </form>
  )
}
