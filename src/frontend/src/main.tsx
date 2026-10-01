import { StrictMode, useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'

function App() {
  const [status, setStatus] = useState('Connecting…')

  useEffect(() => {
    const controller = new AbortController()
    fetch('/api/health', { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error('Service unavailable')
        const health = await response.json()
        if (health.status !== 'ok' || health.database !== 'connected') {
          throw new Error('Unexpected health response')
        }
        setStatus('Connected and ready.')
      })
      .catch(() => {
        if (!controller.signal.aborted) setStatus('Unable to connect. Please refresh to try again.')
      })
    return () => controller.abort()
  }, [])

  return (
    <main style={{ maxWidth: 720, margin: '4rem auto', padding: '0 1rem', fontFamily: 'system-ui' }}>
      <h1>Lost In Translation</h1>
      <p>A language learning scavenger hunt.</p>
      <p role="status">{status}</p>
    </main>
  )
}

createRoot(document.getElementById('root')!).render(
  <StrictMode><App /></StrictMode>,
)
