import { useRef, useState, type FormEvent } from 'react'
import { LANGUAGES } from '../utils/languages'

interface Props {
  disabled: boolean
  onStart: (language: string, difficulty: string) => Promise<void>
  onCancel: () => void
}

export default function StartGameForm({ disabled, onStart, onCancel }: Props) {
  const [language, setLanguage] = useState('fr')
  const [difficulty, setDifficulty] = useState('basic')
  const inFlight = useRef(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (disabled || inFlight.current) return
    inFlight.current = true
    try { await onStart(language, difficulty) }
    finally { inFlight.current = false }
  }

  return (
    <form onSubmit={submit} aria-label="Start a game">
      <p><label htmlFor="game-language">Language </label>
        <select id="game-language" value={language} onChange={(e) => setLanguage(e.target.value)} disabled={disabled}>
          {Object.entries(LANGUAGES).map(([code, name]) => <option key={code} value={code}>{name}</option>)}
        </select></p>
      <p><label htmlFor="game-difficulty">Difficulty </label>
        <select id="game-difficulty" value={difficulty} onChange={(e) => setDifficulty(e.target.value)} disabled={disabled}>
          <option value="basic">Basic — numbers only</option>
          <option value="advanced">Advanced — numbers and descriptions</option>
          <option value="expert">Expert — descriptions only</option>
        </select></p>
      <button type="submit" disabled={disabled}>{disabled ? 'Starting game...' : 'Begin hunt'}</button>
      {' '}<button type="button" onClick={onCancel} disabled={disabled}>Cancel</button>
    </form>
  )
}
