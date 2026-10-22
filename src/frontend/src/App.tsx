import { useEffect, useState } from 'react'
import LoadingScreen from './LoadingScreen'

interface HelloResponse {
  message: string
}

export default function App() {
  const [message, setMessage] = useState('Loading...')
  // TEMP: preview of the loading screen. Remove before the real game flow exists.
  const [previewProgress, setPreviewProgress] = useState<number | null>(null)

  useEffect(() => {
    fetch('/api/hello')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json() as Promise<HelloResponse>
      })
      .then((data) => setMessage(data.message))
      .catch((err: Error) => setMessage(`Could not reach backend: ${err.message}`))
  }, [])

  // TEMP: fill the preview bar, then go back to the home page when it reaches 100
  useEffect(() => {
    if (previewProgress === null) return
    if (previewProgress >= 100) {
      const done = setTimeout(() => setPreviewProgress(null), 600)
      return () => clearTimeout(done)
    }
    const step = setTimeout(() => setPreviewProgress(previewProgress + 10), 300)
    return () => clearTimeout(step)
  }, [previewProgress])

  if (previewProgress !== null) {
    return <LoadingScreen progress={previewProgress} />
  }

  return (
    <main className="screen">
      <p className="eyebrow">Language learning meets adventure</p>
      <h1>Lost In Translation</h1>
      <p>Listen, explore, and learn through real-world scavenger hunts.</p>
      <p>Your React frontend is ready. Gameplay is coming soon.</p>
      <p>Backend says: {message}</p>
      <button className="game-button" onClick={() => setPreviewProgress(0)}>
        Preview loading screen
      </button>
    </main>
  )
}