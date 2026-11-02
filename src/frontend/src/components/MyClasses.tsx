import type { StudentClass } from '../api/profile'
import { languageName } from '../utils/languageName'

interface Props {
  classes: StudentClass[]
}

export default function MyClasses({ classes }: Props) {
  return (
    <>
      <h2>My classes</h2>
      {classes.length === 0 ? (
        <p>You're not in any classes yet.</p>
      ) : (
        <ul>
          {classes.map((classroom) => (
            <li key={classroom.id}>{classroom.name} · {languageName(classroom.language_code)}</li>
          ))}
        </ul>
      )}
    </>
  )
}
