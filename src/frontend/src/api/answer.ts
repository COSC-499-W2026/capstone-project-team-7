export interface AnswerResult {
  correct: boolean
  attempts: number
  finished: boolean
  next_position: number | null
  points_awarded: number
  total_points: number
  message: string
}

export async function submitAnswer(gameId: string, photo: File): Promise<AnswerResult> {
  if (photo.size > 5 * 1024 * 1024) throw new Error('Photo is too large. Please retake it.')
  const res = await fetch(`/api/game/${gameId}/answer`, {
    method: 'POST', credentials: 'same-origin',
    headers: { 'Content-Type': photo.type || 'image/jpeg' }, body: photo,
  }).catch(() => { throw new Error('Could not send your photo. Please try again.') })
  if (res.status === 401) throw new Error('Please log in again')
  const body = await res.json().catch(() => null)
  if (!res.ok) throw new Error(typeof body?.detail === 'string' ? body.detail : 'Could not verify your photo. Please try again.')
  if (!body || typeof body.correct !== 'boolean' || typeof body.finished !== 'boolean' ||
      !Number.isSafeInteger(body.points_awarded) || !Number.isSafeInteger(body.total_points) ||
      (!body.correct && (body.points_awarded !== 0 || body.finished)) ||
      body.points_awarded < 0 || body.total_points < body.points_awarded || typeof body.message !== 'string') {
    throw new Error('Photo verification is unavailable. Please try again later.')
  }
  return body as AnswerResult
}
