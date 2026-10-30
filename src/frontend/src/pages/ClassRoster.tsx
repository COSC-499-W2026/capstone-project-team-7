import { useEffect, useState } from 'react'
import { getClassRoster, type RosterStudent } from '../api/classRoster'
import { SessionEndedError } from '../api/sessionEnded'
import RosterTable from './RosterTable'

interface Props {
  classId: string
  onSessionEnded: () => void
}

export default function ClassRoster({ classId, onSessionEnded }: Props) {
  const [students, setStudents] = useState<RosterStudent[] | null>(null)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let active = true
    setStudents(null)
    setError('')
    getClassRoster(classId).then((items) => {
      if (active) setStudents(items)
    }).catch((err) => {
      if (!active) return
      if (err instanceof SessionEndedError) onSessionEnded()
      else setError(err instanceof TypeError ? 'Could not load students, please try again' : (err as Error).message)
    })
    return () => { active = false }
  }, [classId, onSessionEnded, attempt])

  return (
    <section className="teacher-roster" aria-label="Class roster">
      <h2>Class roster</h2>
      {error ? <p role="alert">{error} <button onClick={() => setAttempt(attempt + 1)}>Reload students</button></p>
        : students === null ? <p role="status">Loading students…</p>
        : <RosterTable students={students} />}
    </section>
  )
}
