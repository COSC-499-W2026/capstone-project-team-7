// Sends the student's photo for the current spot and gets back whether it was right.

export interface AnswerResult {
  correct: boolean
  attempts: number
  finished: boolean
  next_position: number | null
}

export async function submitAnswer(gameId: string, photo: File): Promise<AnswerResult> {
  const res = await fetch(`/api/game/${gameId}/answer`, {
    method: 'POST',
    headers: { 'Content-Type': photo.type || 'image/jpeg' },
    body: photo,
  })

  if (res.status === 401) throw new Error('Please log in again')
  if (!res.ok) {
    // The backend's messages are already friendly (e.g. "Photo is too large"), so show them.
    const body = await res.json().catch(() => null)
    throw new Error(body?.detail ?? 'Could not send your photo, please try again')
  }

  return res.json() as Promise<AnswerResult>
}
