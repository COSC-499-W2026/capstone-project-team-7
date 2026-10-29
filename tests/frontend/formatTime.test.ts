import { expect, test } from 'vitest'
import { formatTime } from '../../src/frontend/src/utils/formatTime'

test.each([[0, '0:00'], [9, '0:09'], [75, '1:15'], [3599, '59:59'], [3725, '1:02:05']])(
  'shows %s seconds as %s', (seconds, shown) => {
    expect(formatTime(seconds)).toBe(shown)
  })

test('never shows a negative or fractional time', () => {
  expect(formatTime(-5)).toBe('0:00')
  expect(formatTime(61.9)).toBe('1:01')
})
