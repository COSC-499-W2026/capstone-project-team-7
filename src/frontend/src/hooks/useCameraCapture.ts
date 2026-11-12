import { useEffect, useRef, useState } from 'react'

// Turns a camera error into a message the player can act on
export function cameraErrorMessage(error: unknown) {
  const name = (error as { name?: string } | null)?.name
  if (name === 'NotAllowedError') return 'We need your camera to check the room number. Please allow camera access and try again.'
  if (name === 'NotFoundError') return "We couldn't find a camera on this device."
  return "Your camera couldn't start. Please try again."
}

export function useCameraCapture() {
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

  function onPlaying() {
    setCameraReady(true)
  }

  return { videoRef, cameraReady, photo, previewUrl, error, takePhoto, retake, tryCameraAgain, onPlaying }
}
