import type { CSSProperties } from 'react'
import iconsUrl from '../assets/profile-icons.png'

// The order of tiles in profile-icons.png: one row per language (fr, es, de, zh, ja, ko), three icons each.
const SHEET = [
  ['croissant_cutie', 'mac_the_macaron', 'speedy_escargot'],
  ['taco_tuesday', 'chili_chill', 'llama_drama'],
  ['gummibar', 'cuckoo_buddy', 'doxie_the_dachshund'],
  ['dumpling_darling', 'lucky_koi', 'panda_pal'],
  ['rice_ball_buddy', 'lucky_cat', 'shiba_smile'],
  ['bibimbap_buddy', 'dalgona_star', 'horangi_the_tiger'],
]

interface Props {
  id: string
  name: string
  size: number
  locked?: boolean
}

// Sizes and positions are percentages so the same sheet works at any icon size.
export function profileIconStyle(id: string, size: number, locked = false): CSSProperties {
  const row = SHEET.findIndex((icons) => icons.includes(id))
  const style: CSSProperties = { width: size, height: size }
  if (row === -1) {
    style.border = '1px solid #c9dfd2'
    style.borderRadius = '50%'
  } else {
    const column = SHEET[row].indexOf(id)
    style.backgroundImage = `url(${iconsUrl})`
    style.backgroundSize = `${SHEET[0].length * 100}% ${SHEET.length * 100}%`
    style.backgroundPosition = `${column * 50}% ${row * 20}%`
  }
  if (locked) {
    style.filter = 'grayscale(1)'
    style.opacity = 0.4
  }
  return style
}

export default function ProfileIcon({ id, name, size, locked = false }: Props) {
  return <div role="img" aria-label={name} style={profileIconStyle(id, size, locked)} />
}
