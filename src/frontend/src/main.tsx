import React from 'react'
import ReactDOM from 'react-dom/client'
import './style.css'

function App() {
  return (
    <main>
      <p className="eyebrow">Language learning meets adventure</p>
      <h1>Lost In Translation</h1>
      <p>Listen, explore, and learn through real-world scavenger hunts.</p>
      <p>Your React frontend is ready. Gameplay is coming soon.</p>
    </main>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><App /></React.StrictMode>,
)
