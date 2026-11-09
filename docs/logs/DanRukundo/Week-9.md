# Week 9 Individual Log: Dan Rukundo

November 2–8, 2026 | Team 7 | Lost In Translation

## Summary

This week I connected difficulty to the clues students hear and added language and difficulty selection when starting a game. Last week's scoring already used the saved difficulty, but students still started every game in French on Basic. My four merged PRs connect the selection form, backend validation, clue generation and audio playback.

| PR | Issue | Contribution | Status |
|---|---|---|---|
| [#209](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/209) | #207 | Generate difficulty-specific clue text and audio | Merged November 8 |
| [#210](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/210) | #208 | Serve audio using the game's saved difficulty | Merged November 8 |
| [#212](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/212) | #211 | Accept and save language and difficulty at game creation | Merged November 8 |
| [#215](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/215) | #211 | Add the student start-game selection form | Merged November 8 |

## Difficulty-specific clues and audio

In #209, I added a shared clue-text helper and updated the audio generator to follow the existing difficulty rules: Basic contains the room number, Advanced combines the number and description, and Expert contains only the description. Required text cannot be blank. Basic retains its existing audio paths; Advanced and Expert use separate difficulty folders, so generation does not overwrite Basic recordings.

Tests cover valid clue composition, missing required text, audio paths, generation and failure handling. The README and difficulty design document explain the rules and storage layout. One remaining content issue is that LIB 312 and LIB 317 have the same demo description, so their Expert clues need revision to distinguish them.

In #210, I connected the audio endpoint to the difficulty stored on the game. A query parameter cannot change the level, and a missing Advanced or Expert recording returns 404 instead of falling back to an easier clue. An unsupported stored difficulty returns a friendly error. Tests cover playback selection, missing clips, unsupported difficulty and access control.

## Language and difficulty selection

In #212, I updated game creation to validate a choice of six languages and three difficulties, save those choices, and select locations from the chosen language's clue pool. Existing clients can still omit the choices and receive French Basic. Unknown languages, invalid difficulties, null values and unexpected fields are rejected before database access. The positive tests cover all 18 language/difficulty combinations; negative tests check invalid requests.

In #215, I added a separate `StartGameForm` component. Start game opens the form, Begin hunt submits the selected language and difficulty, and Cancel returns without creating a game. Controls are disabled while the request is running, and selections remain available after an error. I also changed the gameplay instruction to “Listen to the clue,” since Expert clues do not contain a room number. Frontend tests cover the form and dashboard request flow.

## Review and collaboration

Gamu requested that I split the initial language/difficulty change into smaller PRs. I kept #212 focused on the backend and moved the frontend into #215, making each part easier to review. Ashish approved both smaller changes and described #210 as small, direct and well tested in his Week 9 log.

For #209, Ashish agreed with Gamu's concern that we need a shared process for generating, distributing and reviewing audio across difficulties. He generated the French demo clips using the script. The code establishes the difficulty rules, but the descriptions and recordings still need content review before the demo. Ashish's log also records my approval of the diagram update in #193.

## Additional work in progress

I also implemented difficulty-based clue replay limits on the `213-limit-clue-audio-replays-by-difficulty` branch. It stores playback counts on the backend so refresh and resume do not reset them, gives each new clue a fresh allowance, and shows remaining plays in the frontend. This branch includes a new migration and tests for the backend limits and playback component. It is separate from the four merged PRs above and is not recorded as completed integration work.

## Testing and verification

The added tests are in `test_clue_text.py`, `test_audio_storage.py`, `test_generate_audio.py`, `test_clue_audio.py`, `test_start_game_choices.py`, `startGameForm.test.ts` and `dashboard.test.ts`. They cover successful behavior and rejected input or unavailable audio.

The replay-limit commit `aa97317` records 744 backend tests and 152 frontend tests passing, plus a successful frontend production build. Those are historical results for that branch, not a fresh run or a result for the final merged application. Teammate logs report that GitHub Actions could not start jobs because of an account billing lock; that is not evidence of passing CI. No new application test result is claimed by this documentation update.

## Architecture and next steps

The flow is now student selection → validated game creation → saved language and difficulty → matching audio playback and existing difficulty-based scoring. Shared clue and audio-path helpers keep generation and playback consistent without adding a second set of difficulty rules.

Next I need to finish reviewing and integrating replay limits, check its migration number against other new migrations, and test it after merging the current application changes. We also need enough locations and recordings for every selectable language, distinct Expert descriptions, and a manual playthrough of the complete selection-to-finish flow. A language being selectable does not establish that its demo content is ready.
