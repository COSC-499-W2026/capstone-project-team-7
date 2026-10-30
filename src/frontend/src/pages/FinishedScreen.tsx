import { formatTime } from '../utils/formatTime'

interface Props {
  totalSpots: number
  totalPoints: number
  timeSeconds: number
  onBack: () => void
}

export default function FinishedScreen({ totalSpots, totalPoints, timeSeconds, onBack }: Props) {
  return (
    <main>
      <h1>You finished!</h1>
      <p>You found all {totalSpots} spots.</p>
      <p role="status">Total: {totalPoints} points.</p>
      <p>Time: {formatTime(timeSeconds)}</p>
      <button onClick={onBack}>Back to dashboard</button>
    </main>
  )
}
