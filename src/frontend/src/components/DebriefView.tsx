import type { Debrief } from '../api/debrief'
import { languageName } from '../utils/languageName'

export default function DebriefView({ debrief }: { debrief: Debrief }) {
  if (debrief.completed_hunts === 0) return <p>Complete a hunt first to see your debrief.</p>
  return <>
    <p>Completed hunts: {debrief.completed_hunts}</p>
    {debrief.difficulties.length === 0 ? <p>No particular difficulties were recorded yet.</p> : <>
      <h2>Areas to review</h2>
      <p>These clues had repeated listens or photo attempts.</p>
      <ul>{debrief.difficulties.map((item) => <li key={`${item.building}-${item.room_number}-${item.language_code}-${item.difficulty}`}>
        <h3>{item.building} {item.room_number} — {languageName(item.language_code)} ({item.difficulty})</h3>
        <p>Clue listens: {item.listens}; photo attempts: {item.attempts} across {item.hunts} {item.hunts === 1 ? 'hunt' : 'hunts'}.</p>
        {item.number_text || item.description_text ? <>
          <p>Vocabulary to review:</p>
          {item.number_text && <p>Number: {item.number_text}</p>}
          {item.description_text && <p>Description: {item.description_text}</p>}
        </> : <p>Vocabulary is unavailable for this clue.</p>}
      </li>)}</ul>
    </>}
  </>
}
