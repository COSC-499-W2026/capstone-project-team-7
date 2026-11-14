import type { RosterStudent } from '../api/teacher'

interface Props { students: RosterStudent[] }

export default function RemovedStudents({ students }: Props) {
  return (
    <section aria-label="Removed students">
      <h3>Removed students</h3>
      <ul>
        {students.map((student) => <li key={student.student_id}>
          {student.first_name} {student.last_name} · {student.student_number}
          {student.unenrolled_at && ` · Removed ${new Date(student.unenrolled_at).toLocaleDateString('en-CA')}`}
        </li>)}
      </ul>
    </section>
  )
}
