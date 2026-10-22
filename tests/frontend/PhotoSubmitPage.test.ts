import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import PhotoSubmitPage, { cameraErrorMessage } from '../../src/frontend/src/PhotoSubmitPage'

function renderPhotoPage() {
  return renderToStaticMarkup(createElement(PhotoSubmitPage, {
    spotNumber: 2, totalSpots: 5, onSubmit: () => {}, onClose: () => {},
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
