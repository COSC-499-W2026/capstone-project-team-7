import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { expect, test, vi } from 'vitest'
import StartGameForm from '../../src/frontend/src/components/StartGameForm'

test('offers six languages and three difficulties', () => {
  const html = renderToStaticMarkup(createElement(StartGameForm, { disabled: false, onStart: vi.fn(), onCancel: vi.fn() }))
  expect(html.match(/<option /g)).toHaveLength(9)
  expect(html).toContain('Expert — descriptions only')
  expect(html).toContain('Begin hunt')
  expect(html).toContain('Cancel')
  expect(html).not.toContain('disabled=""')
})

test('disables choices and actions during startup', () => {
  const html = renderToStaticMarkup(createElement(StartGameForm, { disabled: true, onStart: vi.fn(), onCancel: vi.fn() }))
  expect(html.match(/disabled=""/g)).toHaveLength(4)
  expect(html).toContain('Starting game...')
})
