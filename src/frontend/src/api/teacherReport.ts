// Asks the backend for a class's progress report, as data for the screen or as a CSV file.

import { apiRequest, type RequestErrors } from './request'

export interface ClueRow { building: string; room_number: string; plays: number }

export interface StudentRow {
  student_id: string
  first_name: string
  last_name: string
  username: string
  total_points: number
  difficulties_completed: string[]
  games_finished: number
  total_game_seconds: number
  // A number of seconds, or "No games completed yet".
  fastest_game_seconds: number | string
  locations_completed: number
  locations_skipped: number
  clue_plays: ClueRow[]
}

export interface Level { building: string; room_number: string; difficulty: string; count: number }

export interface ClassReport {
  students: StudentRow[]
  hardest_levels: { most_skipped: Level[]; most_replayed: Level[]; most_attempts: Level[] }
}

const errors: RequestErrors = {
  fallback: 'Could not load the report, please try again',
  statuses: { 403: 'Teacher access required', 404: 'Class not found' },
}

function reportUrl(classId: string, ending: string) {
  return `/api/teacher/classes/${encodeURIComponent(classId)}/${ending}`
}

export async function getClassReport(classId: string): Promise<ClassReport> {
  const res = await apiRequest(reportUrl(classId, 'report'), undefined, errors)
  return res.json() as Promise<ClassReport>
}

export async function getClassReportCsv(classId: string): Promise<{ file: Blob; filename: string }> {
  const res = await apiRequest(reportUrl(classId, 'report.csv'), undefined, errors)
  // The backend picks the name, e.g. attachment; filename="French-101-report-2026-11-25.csv".
  const match = /filename="([^"]+)"/.exec(res.headers.get('Content-Disposition') ?? '')
  return { file: await res.blob(), filename: match?.[1] ?? 'class-report.csv' }
}
