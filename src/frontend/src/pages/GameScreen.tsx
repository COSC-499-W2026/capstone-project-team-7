import { useEffect, useState } from 'react'
import { getClue, type Clue } from '../api/clue'
import { SessionEndedError } from '../api/sessionEnded'

interface Props {
  gameId: string
  onSubmitPhoto: (clue: Clue) => void
  onBack: () => void
  onSessionEnded: () => void
}

export default function GameScreen({ gameId, onSubmitPhoto, onBack, onSessionEnded }: Props) {
  const [clue, setClue] = useState<Clue | null>(null)
  const [error, setError] = useState('')

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

  return (
    <main>
      <h1>Spot {clue.position} of {clue.total_locations}</h1>
      <p>Building: {clue.building}</p>

      <p>Listen for the room number:</p>
      <audio controls src={clue.audio_url} />

      <p>
        <button onClick={() => onSubmitPhoto(clue)}>Submit photo</button>
      </p>
      <p>
        <button onClick={onBack}>Back to dashboard</button>
      </p>
    </main>
  )
}
