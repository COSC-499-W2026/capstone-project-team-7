import { useEffect, useState, type CSSProperties } from 'react'
import { getBadges, type Badge } from '../api/badges'
import { SessionEndedError } from '../api/sessionEnded'
import badgesUrl from '../assets/badges.png'
import polyglotUrl from '../assets/polyglot.png'
import { languageName } from '../utils/languageName'

interface Props {
  onBack: () => void
  onSessionEnded: () => void
}

// The order of rows and columns of big badges in badges.png (the small copies on its right aren't used).
const ROWS = ['fr', 'es', 'de', 'zh', 'ja', 'ko']
const COLUMNS = ['first_hunt', 'basic', 'advanced', 'expert', 'master']
// Pixel sizes measured from the pictures. polyglot.png has the earned badge first, then its own locked design.
const SHEET = { width: 1935, height: 1779, left: 40, top: 34, stepX: 246, stepY: 286.4, badgeWidth: 205, badgeHeight: 254 }
const POLYGLOT = { width: 1520, height: 680, earnedLeft: 58, lockedLeft: 586, top: 66, badgeWidth: 460, badgeHeight: 550 }
const BADGE_WIDTH = 160
const POLYGLOT_WIDTH = 240

// Turns a badge id like "es_advanced" into its row and column in badges.png, or null if it isn't in the picture.
export function badgeTile(id: string): { row: number; column: number } | null {
  const split = id.indexOf('_')
  const row = ROWS.indexOf(id.slice(0, split))
  const column = COLUMNS.indexOf(id.slice(split + 1))
  if (split === -1 || row === -1 || column === -1) return null
  return { row, column }
}

// Which picture a badge is in, and the box (in pixels) it sits in there. Null if there's no picture for it.
export function badgeSpot(badge: Badge) {
  if (badge.id === 'polyglot') {
    const left = badge.earned ? POLYGLOT.earnedLeft : POLYGLOT.lockedLeft
    return { url: polyglotUrl, sheetWidth: POLYGLOT.width, sheetHeight: POLYGLOT.height, left, top: POLYGLOT.top,
      width: POLYGLOT.badgeWidth, height: POLYGLOT.badgeHeight }
  }
  const tile = badgeTile(badge.id)
  if (!tile) return null
  return { url: badgesUrl, sheetWidth: SHEET.width, sheetHeight: SHEET.height,
    left: SHEET.left + tile.column * SHEET.stepX, top: SHEET.top + Math.round(tile.row * SHEET.stepY),
    width: SHEET.badgeWidth, height: SHEET.badgeHeight }
}

// Shrinks the whole picture so the badge's box is `width` wide, then slides it so only that badge shows.
// Locked badges are grey and faded, except Polyglot, which has its own locked design.
export function badgeStyle(badge: Badge, width = BADGE_WIDTH): CSSProperties {
  const spot = badgeSpot(badge)
  if (!spot) return { width, height: width, border: '1px solid #c9dfd2' }
  const scale = width / spot.width
  const style: CSSProperties = {
    width, height: Math.round(spot.height * scale),
    backgroundImage: `url(${spot.url})`,
    backgroundSize: `${spot.sheetWidth * scale}px ${spot.sheetHeight * scale}px`,
    backgroundPosition: `-${spot.left * scale}px -${spot.top * scale}px`,
  }
  if (!badge.earned && badge.id !== 'polyglot') {
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

  // One badge: its picture (click or hover for what it's for), a lock if it isn't earned yet, and its description once clicked.
  function renderBadge(badge: Badge, width: number) {
    return (
      <div key={badge.id} style={{ position: 'relative', width }}>
        <button
          onClick={() => setOpenId(openId === badge.id ? null : badge.id)}
          title={`${badge.name}: ${badgeDescription(badge)}`}
          style={{ border: 'none', background: 'none', padding: 0, cursor: 'pointer' }}
        >
          <div role="img" aria-label={badge.name} style={badgeStyle(badge, width)}>
            {!badgeSpot(badge) && badge.name}
          </div>
        </button>
        {!badge.earned && badge.id !== 'polyglot' && <span style={{ position: 'absolute', top: 4, right: 4 }}>🔒</span>}
        {openId === badge.id && <p>{badgeDescription(badge)}</p>}
      </div>
    )
  }

  const polyglot = badges?.find((badge) => badge.id === 'polyglot')

  return (
    // Wider than other pages so five badges (one language) fit on each row.
    <main style={{ maxWidth: 960 }}>
      <h1>My badges</h1>
      <button onClick={onBack}>Back</button>
      {error && <p role="alert">{error}</p>}
      {!badges && !error && <p>Loading badges...</p>}
      {badges && (
        <>
          <p>{earnedText(badges)}</p>
          {polyglot && (
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.5rem' }}>
              {renderBadge(polyglot, POLYGLOT_WIDTH)}
            </div>
          )}
          <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '1rem' }}>
            {badges.filter((badge) => badge.id !== 'polyglot').map((badge) => renderBadge(badge, BADGE_WIDTH))}
          </div>
        </>
      )}
    </main>
  )
}
