const languageNames = new Intl.DisplayNames(['en'], { type: 'language' })

// e.g. "fr" -> "French"; falls back to the code if the browser doesn't know it.
export function languageName(code: string) {
  return languageNames.of(code) ?? code
}
