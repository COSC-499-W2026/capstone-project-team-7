import { useEffect, useState } from 'react'
import { getClue, skipClue, type Clue } from '../api/clue'
import { quitGame } from '../api/game'
import { SessionEndedError } from '../api/sessionEnded'
import CluePlayer from '../components/CluePlayer'
import Stopwatch from '../components/Stopwatch'

interface Props {
  gameId: string
  notice?: string
  onSubmitPhoto: (clue: Clue) => void
  onBack: () => void
  onSessionEnded: () => void
}

export default function GameScreen({ gameId, notice, onSubmitPhoto, onBack, onSessionEnded }: Props) {
  const [clue, setClue] = useState<Clue | null>(null)
  const [error, setError] = useState('')
  // After "Back to dashboard": show Save for later / Quit game / Keep playing.
  const [leaving, setLeaving] = useState(false)
  const [quitting, setQuitting] = useState(false)
  const [quitError, setQuitError] = useState('')
  const [skipping, setSkipping] = useState(false)
  const [skipError, setSkipError] = useState('')

  useEffect(() => {
    let leftPage = false // don't update the page if the student already left it
    getClue(gameId)
      .then((result) => { if (!leftPage) setClue(result) })
      .catch((err: Error) => {
        if (leftPage) return
        if (err instanceof SessionEndedError) onSessionEnded()
        else setError(err.message)
      })
    return () => { leftPage = true }
  }, [gameId, onSessionEnded])

  // Quit the game for good, then go back. If it fails, stay here and say why.
  async function handleQuit() {
    setQuitting(true)
    setQuitError('')
    try {
      await quitGame(gameId)
      onBack()
    } catch (err) {
      if (err instanceof SessionEndedError) onSessionEnded()
      else setQuitError((err as Error).message)
      setQuitting(false)
    }
  }

  if (error) {
    return (
      <main>
        <p role="alert">{error}</p>
        <button onClick={onBack}>Back to dashboard</button>
      </main>
    )
  }

  if (!clue) {
    return <main><p>Loading clue...</p></main>
  }

  async function handleSkip(currentClue: Clue) {
    setSkipping(true)
    setSkipError('')
    try {
      setClue(await skipClue(gameId, currentClue))
    } catch (err) {
      if (err instanceof SessionEndedError) onSessionEnded()
      else setSkipError((err as Error).message)
    } finally {
      setSkipping(false)
    }
  }

  return (
    <main>
      {notice && <p role="status">{notice}</p>}
      <h1>Spot {clue.position} of {clue.total_locations}</h1>
      <Stopwatch startSeconds={clue.elapsed_seconds} />
      {clue.building && <p>Building: {clue.building}</p>}

      <p>Listen to the clue:</p>
      <CluePlayer key={`${gameId}:${clue.position}:${clue.clue_id}`} gameId={gameId} clue={clue} />

      <p>
        <button onClick={() => onSubmitPhoto(clue)} disabled={skipping || quitting}>Submit photo</button>
        {' '}
        <button onClick={() => handleSkip(clue)} disabled={skipping || quitting || leaving}>
          {skipping ? 'Replacing location...' : 'Skip location'}
        </button>
      </p>
      {skipError && <p role="alert">{skipError}</p>}
      {leaving ? (
        <section aria-label="Leave game">
          <p>Leave this game?</p>
          <p><button onClick={onBack} disabled={quitting}>Save for later</button></p>
          <p>
            <button onClick={handleQuit} disabled={quitting}>{quitting ? 'Quitting...' : 'Quit game'}</button>
            {' '}You'll lose the points from this game.
          </p>
          <p><button onClick={() => { setLeaving(false); setQuitError('') }} disabled={quitting}>Keep playing</button></p>
          {quitError && <p role="alert">{quitError}</p>}
        </section>
      ) : (
        <p>
          <button onClick={() => setLeaving(true)} disabled={skipping}>Back to dashboard</button>
        </p>
      )}
    </main>
  )
}
