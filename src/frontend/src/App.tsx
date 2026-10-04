import { useEffect, useState } from 'react'

interface HelloResponse {
  message: string
}

export default function App() {
  const [message, setMessage] = useState('Loading...')

  useEffect(() => {
    fetch('/api/hello')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json() as Promise<HelloResponse>
      })
      .then((data) => setMessage(data.message))
      .catch((err: Error) => setMessage(`Could not reach backend: ${err.message}`))
  }, [])

  return (
    <main>
      <p className="eyebrow">Language learning meets adventure</p>
      <h1>Lost In Translation</h1>
      <p>Listen, explore, and learn through real-world scavenger hunts.</p>
      <p>Your React frontend is ready. Gameplay is coming soon.</p>
      <p>Backend says: {message}</p>
    </main>
  )
}
