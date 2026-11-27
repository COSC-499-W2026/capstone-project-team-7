import type { ClassReport, Level } from '../api/teacherReport'

interface Props {
  classTitle: string
  report: ClassReport | null
  error: string
  busy: boolean
  onDownload: () => void
  onBack: () => void
}

// 750 -> "12m 30s", 3725 -> "1h 2m 5s". Text like "No games completed yet" is shown as it is.
export function readableTime(seconds: number | string) {
  if (typeof seconds === 'string') return seconds
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const rest = `${minutes}m ${seconds % 60}s`
  return hours > 0 ? `${hours}h ${rest}` : rest
}

// Layout only (no new colours or fonts): wider than the other demo pages so the 10 columns fit.
const page = { maxWidth: '72rem', margin: '2rem auto', padding: 'clamp(1rem, 4vw, 2rem)' }
// On narrow screens the table scrolls sideways instead of squashing its columns.
const scroll = { overflowX: 'auto' as const }
const cell = { padding: '0.5rem 0.75rem', verticalAlign: 'top' }
const plainList = { listStyle: 'none', margin: 0, padding: 0, whiteSpace: 'nowrap' as const }
// The three lists sit side by side when there's room and stack on a phone.
const levelGrid = { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(14rem, 1fr))', gap: '0 2rem' }

function capitalize(text: string) {
  return text.charAt(0).toUpperCase() + text.slice(1)
}

function LevelList({ title, levels }: { title: string; levels: Level[] }) {
  return <section>
    <h3>{title}</h3>
    {levels.length === 0 ? <p>None yet.</p> : <ul>
      {levels.map((level) => <li key={`${level.building}-${level.room_number}-${level.difficulty}`}>
        {level.building} {level.room_number} · {capitalize(level.difficulty)} · {level.count}
      </li>)}
    </ul>}
  </section>
}

export default function ClassReportView({ classTitle, report, error, busy, onDownload, onBack }: Props) {
  return (
    <main className="leaderboard" style={page}>
      <h1>Class report</h1>
      <p><button onClick={onBack}>Back</button></p>
      <h2>{classTitle}</h2>
      {error && <p role="alert">{error}</p>}
      {!report && !error && <p role="status">Loading report...</p>}
      {report && <>
        <p><button onClick={onDownload} disabled={busy}>Download CSV</button></p>
        {report.students.length === 0 ? <p>No students in this class yet.</p> : <div style={scroll}><table style={{ minWidth: '60rem' }}>
          <thead><tr>
            <th scope="col" style={cell}>Full name</th><th scope="col" style={cell}>Username</th><th scope="col" style={cell}>Total points</th>
            <th scope="col" style={cell}>Difficulties completed</th><th scope="col" style={cell}>Games finished</th>
            <th scope="col" style={cell}>Total time</th><th scope="col" style={cell}>Fastest time</th>
            <th scope="col" style={cell}>Locations completed</th><th scope="col" style={cell}>Locations skipped</th>
            <th scope="col" style={cell}>Audio plays per clue</th>
          </tr></thead>
          <tbody>{report.students.map((student) => <tr key={student.student_id}>
            <th scope="row" style={cell}>{student.first_name} {student.last_name}</th>
            <td style={cell}>{student.username}</td>
            <td style={cell}>{student.total_points}</td>
            <td style={cell}>{student.difficulties_completed.map(capitalize).join(', ')}</td>
            <td style={cell}>{student.games_finished}</td>
            <td style={cell}>{readableTime(student.total_game_seconds)}</td>
            <td style={cell}>{readableTime(student.fastest_game_seconds)}</td>
            <td style={cell}>{student.locations_completed}</td>
            <td style={cell}>{student.locations_skipped}</td>
            <td style={cell}><ul style={plainList}>{student.clue_plays.map((clue) => <li key={`${clue.building}-${clue.room_number}`}>
              {clue.building} {clue.room_number}: {clue.plays}
            </li>)}</ul></td>
          </tr>)}</tbody>
        </table></div>}
        <h2>Hardest levels</h2>
        <div style={levelGrid}>
          <LevelList title="Most skipped" levels={report.hardest_levels.most_skipped} />
          <LevelList title="Most replayed audio" levels={report.hardest_levels.most_replayed} />
          <LevelList title="Most photo attempts" levels={report.hardest_levels.most_attempts} />
        </div>
      </>}
    </main>
  )
}
