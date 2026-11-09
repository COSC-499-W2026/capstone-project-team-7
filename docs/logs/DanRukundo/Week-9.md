# Week 9 Individual Log: Dan Rukundo

November 2–8, 2026 | Team 7 | Lost In Translation

## Summary

This week I connected difficulty to the clues students hear and added language and difficulty selection when starting a game. Last week's scoring already used the saved difficulty, but students still started every game in French on Basic. My four merged PRs connect the selection form, backend validation, clue generation and audio playback.

| PR | Issue | Contribution | Final GitHub size | Reviewers | Status |
|---|---|---|---|---|---|
| [#209](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/209) | #207 | Generate difficulty-specific clue text and audio | 8 files, +149/−14 | Gamu, Ashish | Merged November 8 |
| [#210](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/210) | #208 | Serve audio using the game's saved difficulty | 4 files, +105/−3 | Gamu, Ashish | Merged November 8 |
| [#212](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/212) | #211 | Accept and save language and difficulty at game creation | 4 files, +95/−12 | Gamu, Ashish | Merged November 8 |
| [#215](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/215) | #211 | Add the student start-game selection form | 10 files, +191/−19 | Gamu, Ashish | Merged November 8 |

The sizes above are the final GitHub PR totals. #215 includes the backend selection commits from #212; its frontend-only commit `c9a0d3d` changes seven files, with 96 additions and seven deletions. #209 and #210 also contain the same compatible audio-path helper update. These totals should not be added together as independent contributions. Although splitting #212 reduced its final scope to four files, GitHub still reports ten files for the stacked #215.

## PR #209: Difficulty-specific clue generation

In #209, I added a shared clue-text helper and updated the audio generator to follow the existing difficulty rules: Basic contains the room number, Advanced combines the number and description, and Expert contains only the description. Required text cannot be blank. Basic retains its existing audio paths; Advanced and Expert use separate difficulty folders, so Advanced and Expert clips do not overwrite Basic clips. Running the full generator still regenerates Basic recordings.

Tests cover valid clue composition, missing required text, audio paths, generation and failure handling. The README and difficulty design document explain the rules and storage layout. One remaining content issue is that LIB 312 and LIB 317 have the same demo description, so their Expert clues need revision to distinguish them.

**Code quality and data.** `utils/clue_text.py` reuses `get_clue_rules` and `Difficulty` rather than duplicating the difficulty definitions. Generation and playback share `audio_path`, with `AUDIO_DIR` deciding the root folder. The generator remains a French demo-content tool using the existing speech-generation setup; it does not provide recordings for all six selectable languages. There is no schema change or new runtime dependency in this PR.

**Review and response.** [Gamu approved #209](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/209), noting that retaining Basic paths protects existing gameplay and teacher uploads. She pointed out that Advanced/Expert recordings must actually be generated and placed where Docker reads them, and that LIB 312 and LIB 317 sound the same on Expert. [Ashish's approval](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/209) added the need for a shared audio-distribution process. His log records generating the 15 French demo clips; that was his content-generation contribution using my script.

## PR #210: Serve audio by saved difficulty

In #210, I connected the audio endpoint to the difficulty stored on the game. A query parameter cannot change the level, and a missing Advanced or Expert recording returns 404 instead of falling back to an easier clue. An unsupported stored difficulty returns a friendly error. Tests cover playback selection, missing clips, unsupported difficulty and access control.

**Code quality and data.** The route reuses the existing current-location lookup and shared audio-path helper. Difficulty comes from `game_sessions`, while the recording remains in file storage. No migration is needed. Invalid stored difficulty returns 500 with “Could not select clue audio. Please try again later.” Existing 401, 403, 404, 409 and 503 access/error behavior is preserved.

**Review.** [Gamu approved #210](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/210), highlighting that the URL cannot override difficulty and missing clips do not fall back to Basic. Ashish also approved, noting the small implementation, reuse and test coverage.

## PR #212: Backend language and difficulty selection

In #212, I updated game creation to validate a choice of six languages and three difficulties, save those choices, and select locations from the chosen language's clue pool. Existing clients can still omit the choices and receive French Basic. Unknown languages, invalid difficulties, null values and unexpected fields are rejected before database access. The positive tests cover all 18 language/difficulty combinations; negative tests check invalid requests.

**Code quality and data.** The Pydantic request model rejects unexpected fields and reuses the existing `Difficulty` enum. Parameterized SQL filters `location_clues` by language and saves the choices in the existing `game_sessions` columns. No migration is required. Authentication and student-role checks continue through the existing dependency. A language without five available locations returns 409 instead of starting an incomplete hunt.

**Review and revision.** [Gamu requested a split](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/212) because the initial combined change touched ten files. I removed the frontend from #212 and submitted it as #215. Gamu and Ashish then approved the smaller backend PR. Gamu also noted that only French had demo locations and that the frontend and backend maintain separate language lists; sharing one source remains a follow-up.

## PR #215: Frontend start-game form

In #215, I added a separate `StartGameForm` component. Start game opens the form, Begin hunt submits the selected language and difficulty, and Cancel returns without creating a game. Controls are disabled while the request is running, and selections remain available after an error. I also changed the gameplay instruction to “Listen to the clue,” since Expert clues do not contain a room number. Frontend tests cover the form and dashboard request flow.

**Code quality.** `StartGameForm.tsx` owns the selection controls and calls the existing game API helper. It reuses the frontend `LANGUAGES` mapping. An `inFlight` ref prevents a second submission before the loading state updates. Friendly API messages distinguish invalid choices (422), insufficient locations (409), an ended session (401), and network/server failures.

**Review.** [Ashish approved the frontend split](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/215), acknowledging the difficulty of keeping frontend changes small. Gamu also approved. The screenshots remain attached to #212, as referenced in #215's description:

![Language and difficulty selection screenshot attached to PR #212](https://github.com/user-attachments/assets/26250b60-57ea-41c7-8f32-bee1121926d8)

![Second start-game screenshot attached to PR #212](https://github.com/user-attachments/assets/7b70eb1f-e6f6-4556-945c-88c0ad4afe53)

These screenshots document the interface; they do not establish a successful full hunt for every language or difficulty.

## Reviews I gave

GitHub records the following 11 approvals from me during this reporting week. Most comments are brief approvals; I am not claiming additional testing or technical findings beyond what the reviews record.

| PR | Teammate's contribution | My recorded review |
|---|---|---|
| [#193](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/193) | Gamu's documentation merge, including Ashish's diagrams | Approved and thanked the team for the merge |
| [#194](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/194) | Gamu's badges page | Approved the badges UI |
| [#196](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/196) | Gamu's teacher assignment form | Approved |
| [#198](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/198) | Ashish's profile icon backend | Approved |
| [#200](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/200) | Ashish's icon artwork and demo seed | Approved |
| [#204](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/204) | Gamu's assigned-hunt list and removal | Approved |
| [#205](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/205) | Gamu's points-redemption endpoints | Approved |
| [#206](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/206) | Gamu's store page | Approved |
| [#217](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/217) | Madiba's class leaderboard API | Approved and reminded him to resolve merge conflicts before merging |
| [#219](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/219) | Madiba's class leaderboard screen | Approved |
| [#221](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/221) | Madiba's admin dashboard | Approved |

## Additional work in progress

I also implemented difficulty-based clue replay limits on the `213-limit-clue-audio-replays-by-difficulty` branch. It stores playback counts on the backend so refresh and resume do not reset them, gives each new clue a fresh allowance, and shows remaining plays in the frontend. This branch includes a new migration and tests for the backend limits and playback component. It is separate from the four merged PRs above and is not recorded as completed integration work.

## Testing and verification

**Positive and negative test evidence.** The merged code contains these concrete checks:

| PR | Positive cases | Negative cases | Test type and location |
|---|---|---|---|
| #209 | `test_clue_contains_exactly_the_required_content` checks all three levels; `test_generates_distinct_clips_with_each_levels_content` checks all five demo locations at each level | `test_missing_required_content_is_rejected`, `test_unknown_difficulty_is_rejected`, `test_generation_failure_is_reported` | Unit tests in `tests/backend/test_clue_text.py`, `test_generate_audio.py` and `test_audio_storage.py`; speech generation is mocked and files use a temporary directory |
| #210 | `test_playback_uses_saved_difficulty` checks all levels, including a misleading `?difficulty=basic` | `test_missing_clip_does_not_fall_back`, `test_invalid_saved_difficulty_is_a_safe_error`, `test_game_access_errors_are_preserved`, `test_non_students_cannot_play_audio`, `test_audio_requires_login` | FastAPI route tests in `tests/backend/test_clue_audio.py`; current-location lookup is mocked and recordings are temporary test bytes |
| #212 | `test_choices_select_pool_and_are_saved` checks all 18 combinations, the selected pool and saved values | `test_invalid_choices_never_reach_database` checks unknown language, invalid difficulty, null values and an unexpected `points` field | Unit/route tests in `tests/backend/test_start_game_choices.py`, using `FakeConnection` and `monkeypatch` rather than PostgreSQL |
| #215 | `offers six languages and three difficulties`, `disables choices and actions during startup`, and `start game sends the chosen language and difficulty` | `invalid selections have a helpful message`, `network errors have a helpful message`, plus existing insufficient-location, expired-session and server-error cases | Frontend tests in `tests/frontend/startGameForm.test.ts` and `dashboard.test.ts`, using static markup and mocked fetch |

**Limits of this evidence.** The frontend tests verify rendered controls and API requests; they do not click Cancel or Begin hunt in a browser, prove error-state retention through an interaction, or complete a GPS/photo hunt. The generation tests mock speech synthesis and do not evaluate pronunciation or whether descriptions uniquely identify rooms. Those need manual checks. No new manual playthrough is claimed here.

The replay-limit commit `aa97317` records 744 backend tests and 152 frontend tests passing, plus a successful frontend production build. Those are historical results for that branch, not a fresh run or a result for the final merged application. Teammate logs report that GitHub Actions could not start jobs because of an account billing lock; that is not evidence of passing CI. No new application test result is claimed by this documentation update.

## Accomplishments and architecture

The four final merged heads are #209 `a812402`, #210 `821a122`, #212 `887a21d` and #215 `c9a0d3d`. All four merged into `main` on November 8. They complete the language/difficulty selection and matching-audio implementation planned after Week 8. Replay limits remain separate work.

In the game DFD, #212 and #215 belong to game creation, while #210 supplies audio for presenting the current location. #209 prepares the audio files consumed by that flow. The browser sends choices; the backend validates them, reads language-specific clues and writes the game configuration. Generation writes recordings to file storage, and authenticated playback reads the game configuration and corresponding file. These four merged PRs introduce no database migration.

## Next steps

The flow is now student selection → validated game creation → saved language and difficulty → matching audio playback and existing difficulty-based scoring. This exposes last week's Basic/Advanced/Expert scoring through the normal start flow; the resulting points also feed Gamu's store and Madiba's leaderboard. Shared clue and audio-path helpers keep generation and playback consistent without adding a second set of difficulty rules.

Next I need to finish reviewing and integrating replay limits, check its migration number against other new migrations, and test it after merging the current application changes. We also need enough locations and recordings for every selectable language, distinct Expert descriptions, and a manual playthrough of the complete selection-to-finish flow. A language being selectable does not establish that its demo content is ready.
