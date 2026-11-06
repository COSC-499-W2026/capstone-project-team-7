import { useEffect, useState } from 'react'
import { formatTime } from '../utils/formatTime'

interface Props {
  startSeconds: number
}

// Counts up from the backend's elapsed time, so a wrong phone clock can't change the total.
export default function Stopwatch({ startSeconds }: Props) {
  const [seconds, setSeconds] = useState(startSeconds)

  useEffect(() => {
    const shownAt = Date.now()
    setSeconds(startSeconds)
    const timer = setInterval(() => setSeconds(startSeconds + Math.floor((Date.now() - shownAt) / 1000)), 1000)
    return () => clearInterval(timer)
  }, [startSeconds])

  return <p role="timer">Time: {formatTime(seconds)}</p>
}
