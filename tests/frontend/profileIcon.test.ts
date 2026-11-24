import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { expect, test } from 'vitest'
import defaultIconUrl from '../../src/frontend/src/assets/default-profile-icon.svg'
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

test('finds an icon in a middle tile', () => {
  expect(profileIconStyle('cuckoo_buddy', 96).backgroundPosition).toBe('50% 40%')
})

test('keeps the same tile at a different size', () => {
  const small = profileIconStyle('speedy_escargot', 40)
  expect(small.backgroundPosition).toBe(profileIconStyle('speedy_escargot', 96).backgroundPosition)
  expect(small.width).toBe(40)
})

test('a student with no equipped icon gets the default icon', () => {
  const style = profileIconStyle('', 40)
  expect(style.backgroundImage).toBe(`url("${defaultIconUrl}")`)
  expect(style.backgroundSize).toBe('cover')
  expect(style.width).toBe(40)
})

test('an unknown id shows the default icon instead of the wrong picture', () => {
  expect(profileIconStyle('not_an_icon', 96).backgroundImage).toBe(`url("${defaultIconUrl}")`)
})

test('an equipped icon replaces the default icon', () => {
  expect(profileIconStyle('croissant_cutie', 96).backgroundImage).not.toBe(`url("${defaultIconUrl}")`)
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
