import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import FinishedScreen from '../../src/frontend/src/pages/FinishedScreen'
import PhotoSubmitPage, { cameraErrorMessage } from '../../src/frontend/src/pages/PhotoSubmitPage'

function renderPhotoPage(sending = false) {
  return renderToStaticMarkup(createElement(PhotoSubmitPage, {
    spotNumber: 2, totalSpots: 5, sending, onSubmit: () => {}, onClose: () => {},
  }))
}

test('the page shows the live camera, not a file picker, so old photos cannot be uploaded', () => {
  const html = renderPhotoPage()
  expect(html).toContain('<video')
  expect(html).not.toContain('type="file"')
  expect(html).toContain('Spot 2 of 5')
})

test('the take photo button waits until the camera is ready', () => {
  const html = renderPhotoPage()
  expect(html).toContain('Starting camera...')
  expect(html).toContain('disabled=""')
  expect(html).not.toContain('Submit photo')
})

test('the close button is disabled while a photo is sending', () => {
  expect(renderPhotoPage()).toContain('aria-label="Close"><svg')
  expect(renderPhotoPage(true)).toContain('aria-label="Close" disabled=""><svg')
})

test('blocking camera access explains why the camera is needed', () => {
  expect(cameraErrorMessage({ name: 'NotAllowedError' })).toContain('allow camera access')
})

test('a device with no camera says so', () => {
  expect(cameraErrorMessage({ name: 'NotFoundError' })).toBe("We couldn't find a camera on this device.")
})

test('any other camera problem asks the player to try again', () => {
  expect(cameraErrorMessage({ name: 'NotReadableError' })).toBe("Your camera couldn't start. Please try again.")
  expect(cameraErrorMessage(null)).toBe("Your camera couldn't start. Please try again.")
})


test('the existing finish screen shows server-awarded points', () => {
  const html = renderToStaticMarkup(createElement(FinishedScreen, { totalSpots: 5, totalPoints: 50, onBack: () => {} }))
  expect(html).toContain('You found all 5 spots.')
  expect(html).toContain('Total: 50 points.')
  expect(html).toContain('Back to dashboard')
})


test('explains location access and announces verification while sending', () => {
  expect(renderPhotoPage()).toContain('Please allow location access')
  expect(renderPhotoPage(true)).toContain('Checking your location and room...')
})
