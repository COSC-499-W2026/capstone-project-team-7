// Request a fresh fix for each answer; the server decides whether it is accurate and nearby.
export async function captureLocation(): Promise<URLSearchParams> {
  if (!navigator.geolocation) throw new Error('Location is unavailable. Use a browser with location access on HTTPS or localhost.')
  const position = await new Promise<GeolocationPosition>((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(resolve, (error) => {
      const message = error.code === 1
        ? 'Please allow location access in your browser settings, then submit again.'
        : error.code === 3
          ? 'Finding your location timed out. Please submit again to retry.'
          : 'Could not find your location. Move to a clearer area and submit again.'
      reject(new Error(message))
    }, { enableHighAccuracy: true, maximumAge: 0, timeout: 10000 })
  })
  return new URLSearchParams({
    latitude: String(position.coords.latitude),
    longitude: String(position.coords.longitude),
    accuracy: String(position.coords.accuracy),
    captured_at: new Date(position.timestamp).toISOString(),
  })
}
