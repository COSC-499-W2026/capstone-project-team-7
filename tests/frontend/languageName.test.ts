import { expect, test } from 'vitest'
import { languageName } from '../../src/frontend/src/utils/languageName'

test.each([['fr', 'French'], ['it', 'Italian'], ['qaa', 'qaa']])('language %s displays as %s without an app-maintained list', (code, name) => {
  expect(languageName(code)).toBe(name)
})
