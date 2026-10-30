import type { RosterStudent } from '../api/classRoster'

export default function RosterTable({ students }: { students: RosterStudent[] }) {
  if (students.length === 0) return <p>No students enrolled in this class yet.</p>
  return (
    <div className="roster-scroll" role="region" aria-label="Class roster" tabIndex={0}>
      <table className="roster-table">
        <caption>Enrolled students</caption>
        <thead><tr><th scope="col">Student</th><th scope="col">Student #</th></tr></thead>
        <tbody>{students.map((student) => <tr key={student.student_id}>
          <td><span className="roster-avatar" aria-hidden="true">{student.first_name.charAt(0)}</span>{student.first_name} {student.last_name}</td>
          <td>{student.student_number}</td>
        </tr>)}</tbody>
      </table>
    </div>
  )
}
