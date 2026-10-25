interface Props {
  totalSpots: number
  totalPoints: number
  onBack: () => void
}

export default function FinishedScreen({ totalSpots, totalPoints, onBack }: Props) {
  return (
    <main>
      <h1>You finished!</h1>
      <p>You found all {totalSpots} spots.</p>
      <p role="status">Total: {totalPoints} points.</p>
      <button onClick={onBack}>Back to dashboard</button>
    </main>
  )
}
