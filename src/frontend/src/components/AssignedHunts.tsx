import { hideOverdue, type StudentHunt } from '../api/assignHunt'
import { languageName } from '../utils/languageName'

interface Props {
  hunts: StudentHunt[]
  disabled: boolean
  onPlay: (hunt: StudentHunt) => void
}

// e.g. "French 101 · French · Basic · Due 2026-11-20" (the due date only shows if there is one)
export function huntLabel(hunt: StudentHunt) {
  const language = languageName(hunt.language_code)
  const difficulty = hunt.difficulty.charAt(0).toUpperCase() + hunt.difficulty.slice(1)
  const due = hunt.due_date ? ` · Due ${hunt.due_date}` : ''
  return `${hunt.class_name} · ${language} · ${difficulty}${due}`
}

export default function AssignedHunts({ hunts, disabled, onPlay }: Props) {
  // Today as "YYYY-MM-DD" in the student's time zone, so hunts past their due date are hidden.
  const today = new Date().toLocaleDateString('en-CA')
  const current = hideOverdue(hunts, today)

  return (
    <>
      <h2>Assigned hunts</h2>
      {current.length === 0 ? <p>No assigned hunts right now.</p> : (
        <ul>
          {current.map((hunt) => (
            <li key={hunt.id}>
              {huntLabel(hunt)}{' '}
              <button onClick={() => onPlay(hunt)} disabled={disabled}>Play</button>
            </li>
          ))}
        </ul>
      )}
    </>
  )
}
