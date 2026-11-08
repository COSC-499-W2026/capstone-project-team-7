import type { LeaderboardEntry } from '../api/leaderboard'
import type { StudentClass } from '../api/profile'
import ProfileIcon from './ProfileIcon'
import { languageName } from '../utils/languageName'

interface Props { classroom: StudentClass; entries: LeaderboardEntry[] }

export default function LeaderboardTable({ classroom, entries }: Props) {
  return <>
    <table>
      <caption>{classroom.name} · {languageName(classroom.language_code)}</caption>
      <thead><tr><th scope="col">Rank</th><th scope="col">Icon</th><th scope="col">Student</th><th scope="col">Points</th></tr></thead>
      <tbody>{entries.map((entry) => <tr key={entry.username}>
        <td>{entry.rank}</td>
        <td><ProfileIcon id={entry.profile_icon ?? ''} name={entry.profile_icon ? `${entry.username}'s profile icon` : 'No profile icon'} size={40} /></td>
        <th scope="row" style={{ overflowWrap: 'anywhere' }}>{entry.username}</th><td>{entry.total_points}</td>
      </tr>)}</tbody>
    </table>
    {entries.length === 0 && <p>No students to display.</p>}
  </>
}
