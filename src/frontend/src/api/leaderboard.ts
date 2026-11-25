import { SessionEndedError } from './sessionEnded'

export interface LeaderboardEntry {
  rank: number
  username: string
  total_points: number
  profile_icon: string | null
}

export async function getLeaderboard(classId: string): Promise<LeaderboardEntry[]> {
  let res: Response
  try { res = await fetch(`/api/student/classes/${encodeURIComponent(classId)}/leaderboard`) }
  catch { throw new Error('Could not connect, please try again') }
  if (res.status === 401) throw new SessionEndedError()
  if (!res.ok) throw new Error('Could not load this leaderboard, please try again')
  return res.json() as Promise<LeaderboardEntry[]>
}
