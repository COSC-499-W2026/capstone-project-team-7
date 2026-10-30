import type { OngoingGame } from '../api/ongoingGames'

interface Props {
  games: OngoingGame[]
  disabled: boolean
  onResume: (game: OngoingGame) => void
}

const languageNames = new Intl.DisplayNames(['en'], { type: 'language' })

// e.g. "French · Basic · Spot 2 of 5"
export function gameLabel(game: OngoingGame) {
  const language = languageNames.of(game.language_code) ?? game.language_code
  const difficulty = game.difficulty.charAt(0).toUpperCase() + game.difficulty.slice(1)
  return `${language} · ${difficulty} · Spot ${game.current_position} of ${game.total_locations}`
}

export default function OngoingGames({ games, disabled, onResume }: Props) {
  if (games.length === 0) return null

  return (
    <>
      <h2>Ongoing games</h2>
      <ul>
        {games.map((game) => (
          <li key={game.game_id}>
            {gameLabel(game)}{' '}
            <button onClick={() => onResume(game)} disabled={disabled}>Resume</button>
          </li>
        ))}
      </ul>
    </>
  )
}
