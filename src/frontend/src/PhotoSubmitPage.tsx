import { useEffect, useRef, useState } from 'react'
import './PhotoSubmitPage.css'

// Turns a camera error into a message the player can act on
export function cameraErrorMessage(error: unknown) {
  const name = (error as { name?: string } | null)?.name
  if (name === 'NotAllowedError') return 'We need your camera to check the room number. Please allow camera access and try again.'
  if (name === 'NotFoundError') return "We couldn't find a camera on this device."
  return "Your camera couldn't start. Please try again."
}

interface PhotoSubmitPageProps {
  spotNumber: number
  totalSpots: number
  onSubmit: (photo: File) => void
  onClose: () => void
}

export default function PhotoSubmitPage({ spotNumber, totalSpots, onSubmit, onClose }: PhotoSubmitPageProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [cameraReady, setCameraReady] = useState(false)
  const [cameraAttempt, setCameraAttempt] = useState(0)
  const [photo, setPhoto] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [error, setError] = useState('')

  // Turn on the back camera while there is no photo, and turn it off again when we leave or take one.
  // Only the live camera is used (no file picker), so players can't upload an old photo from their library.
  useEffect(() => {
    if (photo) return
    if (!navigator.mediaDevices) {
      setError(cameraErrorMessage(null)) // the camera only works on https pages (or localhost)
      return
    }
    let stream: MediaStream | null = null
    let leftPage = false
    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: 'environment' }, audio: false })
      .then((cameraStream) => {
        stream = cameraStream
        if (leftPage) stream.getTracks().forEach((track) => track.stop())
        else if (videoRef.current) videoRef.current.srcObject = stream
      })
      .catch((err) => setError(cameraErrorMessage(err)))
    return () => {
      leftPage = true
      stream?.getTracks().forEach((track) => track.stop())
      setCameraReady(false)
    }
  }, [photo, cameraAttempt])

  // Make a temporary web address for the photo so it can be shown, and free it when the photo changes
  useEffect(() => {
    if (!photo) return
    const url = URL.createObjectURL(photo)
    setPreviewUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [photo])

  function takePhoto() {
    const video = videoRef.current
    if (!video || video.videoWidth === 0) return
    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    canvas.getContext('2d')?.drawImage(video, 0, 0)
    canvas.toBlob((blob) => {
      if (blob) setPhoto(new File([blob], 'room-number.jpg', { type: 'image/jpeg' }))
    }, 'image/jpeg', 0.9)
  }

  function retake() {
    setPhoto(null)
    setPreviewUrl('')
  }

  function tryCameraAgain() {
    setError('')
    setCameraAttempt(cameraAttempt + 1)
  }

  return (
    <main className="screen photo-page">
      <header className="photo-header">
        <button className="photo-close" type="button" aria-label="Close" onClick={onClose}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" aria-hidden="true">
            <path d="M6 6l12 12M18 6L6 18" />
          </svg>
        </button>
        <span className="pill">Spot {spotNumber} of {totalSpots}</span>
      </header>

      <div>
        <h1>Snap the room number</h1>
        <p className="subtitle">Fill the frame with the number on the sign and hold your phone steady.</p>
      </div>

      <div className="photo-frame">
        {previewUrl ? (
          <img className="photo-view" src={previewUrl} alt="Your photo of the room number" />
        ) : error ? (
          <div className="photo-empty">
            <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M4 8h3l2-3h6l2 3h3v11H4z" />
              <circle cx="12" cy="13" r="3.5" />
            </svg>
            <span>Camera is off</span>
          </div>
        ) : (
          <video
            ref={videoRef}
            className="photo-view"
            autoPlay
            playsInline
            muted
            onPlaying={() => setCameraReady(true)}
            aria-label="Live camera view"
          />
        )}
        <span className="photo-corner photo-corner--top-left" aria-hidden="true" />
        <span className="photo-corner photo-corner--top-right" aria-hidden="true" />
        <span className="photo-corner photo-corner--bottom-left" aria-hidden="true" />
        <span className="photo-corner photo-corner--bottom-right" aria-hidden="true" />
      </div>

      {error && <p className="error-message" role="alert">{error}</p>}

      <div className="photo-actions">
        {error ? (
          <button className="game-button game-button--yellow" type="button" onClick={tryCameraAgain}>
            Try again
          </button>
        ) : photo ? (
          <>
            <button className="game-button game-button--white" type="button" onClick={retake}>
              Retake photo
            </button>
            <button className="game-button" type="button" onClick={() => onSubmit(photo)}>
              Submit photo
            </button>
          </>
        ) : (
          <button className="game-button game-button--yellow" type="button" onClick={takePhoto} disabled={!cameraReady}>
            {cameraReady ? 'Take photo' : 'Starting camera...'}
          </button>
        )}
      </div>
    </main>
  )
}
