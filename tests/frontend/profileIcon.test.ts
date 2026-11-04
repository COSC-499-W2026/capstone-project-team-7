import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { expect, test } from 'vitest'
import ProfileIcon, { profileIconStyle } from '../../src/frontend/src/components/ProfileIcon'

test('finds an icon in the first tile', () => {
  const style = profileIconStyle('croissant_cutie', 96)
  expect(style.backgroundPosition).toBe('0% 0%')
  expect(style.backgroundSize).toBe('300% 600%')
  expect(style.width).toBe(96)
})

test('finds an icon in the last tile', () => {
  expect(profileIconStyle('horangi_the_tiger', 96).backgroundPosition).toBe('100% 100%')
})

test('keeps the same tile at a different size', () => {
  const small = profileIconStyle('speedy_escargot', 40)
  expect(small.backgroundPosition).toBe(profileIconStyle('speedy_escargot', 96).backgroundPosition)
  expect(small.width).toBe(40)
})

test('an unknown id shows a plain circle instead of the wrong picture', () => {
  const style = profileIconStyle('not_an_icon', 96)
  expect(style.backgroundImage).toBeUndefined()
  expect(style.borderRadius).toBe('50%')
})

test('owned icons keep their colour and locked ones are grey', () => {
  expect(profileIconStyle('mac_the_macaron', 96).filter).toBeUndefined()
  expect(profileIconStyle('mac_the_macaron', 96, true).filter).toBe('grayscale(1)')
})

test('the icon is named for screen readers', () => {
  const html = renderToStaticMarkup(createElement(ProfileIcon, { id: 'mac_the_macaron', name: 'Mac the Macaron', size: 96 }))
  expect(html).toContain('role="img"')
  expect(html).toContain('aria-label="Mac the Macaron"')
})
