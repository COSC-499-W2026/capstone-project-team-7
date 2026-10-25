import type { AnswerResult } from '../api/answer'

interface Props {
  result: AnswerResult
  onContinue: () => void
}

export default function VerificationResult({ result, onContinue }: Props) {
  return (
    <section role={result.correct ? 'status' : 'alert'}>
      <h1>{result.correct ? (result.finished ? 'Hunt complete!' : 'Correct room!') : 'Room not confirmed'}</h1>
      {!result.correct && <p>{result.message}</p>}
      <p>{result.points_awarded} points awarded. Total: {result.total_points} points.</p>
      {result.correct && <button className="game-button" type="button" onClick={onContinue}>
        {result.finished ? 'Back to dashboard' : 'Next clue'}
      </button>}
    </section>
  )
}
