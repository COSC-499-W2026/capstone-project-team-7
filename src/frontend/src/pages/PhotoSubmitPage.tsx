import { useCameraCapture } from '../hooks/useCameraCapture'

interface PhotoSubmitPageProps {
  spotNumber: number
  totalSpots: number
  sending?: boolean
  notice?: string
  onSubmit: (photo: File) => void
  onClose: () => void
}

export default function PhotoSubmitPage({ spotNumber, totalSpots, sending = false, notice, onSubmit, onClose }: PhotoSubmitPageProps) {
  const { videoRef, cameraReady, photo, previewUrl, error, takePhoto, retake, tryCameraAgain, onPlaying } = useCameraCapture()

  return (
    <main className="screen photo-page">
      <header className="photo-header">
        <button className="photo-close" type="button" aria-label="Close" onClick={onClose} disabled={sending}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" aria-hidden="true">
            <path d="M6 6l12 12M18 6L6 18" />
          </svg>
        </button>
        <span className="pill">Spot {spotNumber} of {totalSpots}</span>
      </header>

      <div className="photo-title">
        <h1>Snap the room number</h1>
        <p className="subtitle">Include the building code and room number on the sign, and hold your phone steady.</p>
      </div>

      <div className="photo-frame">
        {previewUrl ? (
          <img className="photo-view" style={{ width: "100%" }} src={previewUrl} alt="Your photo of the room number" />
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
            className="photo-view" style={{ width: "100%" }}
            autoPlay
            playsInline
            muted
            onPlaying={onPlaying}
            aria-label="Live camera view"
          />
        )}
        <span className="photo-corner photo-corner--top-left" aria-hidden="true" />
        <span className="photo-corner photo-corner--top-right" aria-hidden="true" />
        <span className="photo-corner photo-corner--bottom-left" aria-hidden="true" />
        <span className="photo-corner photo-corner--bottom-right" aria-hidden="true" />
      </div>

      <div className="location-status" role="status" aria-live="polite">
        <svg className="location-status-icon" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
          <path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0Z" />
          <circle cx="12" cy="10" r="2.5" />
        </svg>
        <div>
          <strong>{sending ? 'Verifying your answer' : 'Location verification'}</strong>
          <p>{sending ? 'Checking your location and room...' : 'Your location will be checked when you submit. Please allow location access.'}</p>
        </div>
      </div>
      {notice && <p role="alert">{notice}</p>}
      {error && <p className="error-message" role="alert">{error}</p>}

      <div className="photo-actions">
        {error ? (
          <button className="game-button game-button--yellow" type="button" onClick={tryCameraAgain}>
            Try again
          </button>
        ) : photo ? (
          <>
            <button className="game-button game-button--white" type="button" onClick={retake} disabled={sending}>
              Retake photo
            </button>
            <button className="game-button" type="button" onClick={() => onSubmit(photo)} disabled={sending} aria-busy={sending}>
              {sending ? 'Checking location and room...' : 'Submit photo'}
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
