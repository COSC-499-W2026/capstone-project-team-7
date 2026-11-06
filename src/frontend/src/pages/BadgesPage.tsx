import { useEffect, useState, type CSSProperties } from 'react'
import { getBadges, type Badge } from '../api/badges'
import { SessionEndedError } from '../api/sessionEnded'
import badgesUrl from '../assets/badges.png'
import { languageName } from '../utils/languageName'

interface Props {
  onBack: () => void
  onSessionEnded: () => void
}

// The order of rows and columns in badges.png.
const ROWS = ['fr', 'es', 'de', 'zh', 'ja', 'ko']
const COLUMNS = ['first_hunt', 'basic', 'advanced', 'expert', 'master']
const TILE_WIDTH = 160
const TILE_HEIGHT = 202

// Turns a badge id like "es_advanced" into its place in badges.png, or null if it isn't in the picture.
export function badgeTile(id: string): { row: number; column: number } | null {
  if (id === 'polyglot') return { row: 6, column: 0 }
  const split = id.indexOf('_')
  const row = ROWS.indexOf(id.slice(0, split))
  const column = COLUMNS.indexOf(id.slice(split + 1))
  if (split === -1 || row === -1 || column === -1) return null
  return { row, column }
}

// Locked badges are grey and faded; earned ones keep their colour.
export function badgeStyle(badge: Badge): CSSProperties {
  const tile = badgeTile(badge.id)
  const style: CSSProperties = { width: TILE_WIDTH, height: TILE_HEIGHT }
  if (tile) {
    style.backgroundImage = `url(${badgesUrl})`
    style.backgroundPosition = `-${tile.column * TILE_WIDTH}px -${tile.row * TILE_HEIGHT}px`
  } else {
    style.border = '1px solid #c9dfd2'
  }
  if (!badge.earned) {
    style.filter = 'grayscale(1)'
    style.opacity = 0.4
  }
  return style
}

// What the student has to do to earn the badge. These match the rules in src/backend/badges.py.
export function badgeDescription(badge: Badge) {
  if (badge.id === 'polyglot') return 'Complete a full game in every language'
  const language = languageName(badge.language ?? '')
  const kind = badge.id.slice(badge.id.indexOf('_') + 1)
  if (kind === 'first_hunt') return `Complete a full game in ${language} on any difficulty`
  if (kind === 'master') return `Complete a game and find every ${language} location on all three difficulties`
  const level = kind[0].toUpperCase() + kind.slice(1)
  return `Find every ${language} location on ${level} difficulty (across any number of games)`
}

export function earnedText(badges: Badge[]) {
  const earned = badges.filter((badge) => badge.earned).length
  return `You've earned ${earned} of ${badges.length} badges`
}

export default function BadgesPage({ onBack, onSessionEnded }: Props) {
  const [badges, setBadges] = useState<Badge[] | null>(null)
  const [error, setError] = useState('')
  // The badge whose description is showing after a click (null means none).
  const [openId, setOpenId] = useState<string | null>(null)

  useEffect(() => {
    getBadges().then(setBadges).catch((err) => {
      if (err instanceof SessionEndedError) onSessionEnded()
      else setError((err as Error).message)
    })
  }, [])

  return (
    <main>
      <h1>My badges</h1>
      <button onClick={onBack}>Back</button>
      {error && <p role="alert">{error}</p>}
      {!badges && !error && <p>Loading badges...</p>}
      {badges && (
        <>
          <p>{earnedText(badges)}</p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
            {badges.map((badge) => (
              <div key={badge.id} style={{ position: 'relative', width: TILE_WIDTH }}>
                <button
                  onClick={() => setOpenId(openId === badge.id ? null : badge.id)}
                  title={`${badge.name}: ${badgeDescription(badge)}`}
                  style={{ border: 'none', background: 'none', padding: 0, cursor: 'pointer' }}
                >
                  <div role="img" aria-label={badge.name} style={badgeStyle(badge)}>
                    {!badgeTile(badge.id) && badge.name}
                  </div>
                </button>
                {!badge.earned && <span style={{ position: 'absolute', top: 4, right: 4 }}>🔒</span>}
                {openId === badge.id && <p>{badgeDescription(badge)}</p>}
              </div>
            ))}
          </div>
        </>
      )}
    </main>
  )
}
