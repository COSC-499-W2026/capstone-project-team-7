interface Props {
  totalSpots: number
  onBack: () => void
}

export default function FinishedScreen({ totalSpots, onBack }: Props) {
  return (
    <main>
      <h1>You finished!</h1>
      <p>You found all {totalSpots} spots.</p>
      <button onClick={onBack}>Back to dashboard</button>
    </main>
  )
}
