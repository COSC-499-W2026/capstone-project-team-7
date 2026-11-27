import type { HuntClipChoice } from '../api/assignHunt'
import type { OwnClip } from '../api/teacherClips'
import { locationLabel } from './ClueAudioForm'

// Room id to the chosen clip id; rooms left out play the default clip.
export type ClipPicks = Record<string, string>

interface Props {
  clips: OwnClip[]
  difficulty: string
  picks: ClipPicks
  disabled: boolean
  onChange: (picks: ClipPicks) => void
}

// Only rooms where the teacher has a clip for this difficulty get a choice.
export function roomsWithClips(clips: OwnClip[], difficulty: string): OwnClip[][] {
  const rooms = new Map<string, OwnClip[]>()
  for (const clip of clips.filter((item) => item.difficulty === difficulty)) {
    rooms.set(clip.location_id, [...(rooms.get(clip.location_id) ?? []), clip])
  }
  return [...rooms.values()].sort((a, b) => locationLabel(a[0]).localeCompare(locationLabel(b[0])))
}

export function clipChoices(picks: ClipPicks): HuntClipChoice[] {
  return Object.entries(picks).filter(([, clipId]) => clipId)
    .map(([locationId, clipId]) => ({ location_id: locationId, clip_id: clipId }))
}

export default function HuntClipChoices({ clips, difficulty, picks, disabled, onChange }: Props) {
  const rooms = roomsWithClips(clips, difficulty)
  if (rooms.length === 0) return null
  return (
    <fieldset>
      <legend>Clips for this hunt</legend>
      {rooms.map((roomClips) => {
        const room = roomClips[0]
        const id = `hunt-clip-${room.location_id}`
        return (
          <p key={room.location_id}><label htmlFor={id}>{locationLabel(room)} </label>
            <select id={id} value={picks[room.location_id] ?? ''} disabled={disabled}
              onChange={(e) => onChange({ ...picks, [room.location_id]: e.target.value })}>
              <option value="">Default clip</option>
              {roomClips.map((clip) => <option key={clip.id} value={clip.id}>{clip.label}</option>)}
            </select></p>
        )
      })}
    </fieldset>
  )
}
