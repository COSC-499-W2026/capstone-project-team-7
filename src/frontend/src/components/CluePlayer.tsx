import { useRef } from 'react'
import { recordCluePlay, type Clue } from '../api/clue'

export default function CluePlayer({ gameId, clue }: { gameId: string; clue: Clue }) {
  const counted = useRef(false)

  function handlePlaying() {
    if (counted.current) return
    counted.current = true
    // Recording is best-effort and should never interrupt the audio.
    void recordCluePlay(gameId, clue).catch(() => {})
  }

  return (
    <audio controls src={clue.audio_url} onPlaying={handlePlaying}
      onEnded={() => { counted.current = false }} />
  )
}
