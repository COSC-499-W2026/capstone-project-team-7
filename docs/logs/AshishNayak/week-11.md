### Week 11: Ashish Nayak
Nov 16 to Nov 22

**Contents**

1. [Summary](#1-summary)
2. [PR #238: Default profile icon](#2-pr-238-default-profile-icon)
3. [PR #252: Clue audio for each difficulty](#3-pr-252-clue-audio-for-each-difficulty)
4. [PR #258: Games only pick ready locations](#4-pr-258-games-only-pick-ready-locations)
5. [PR #254: Teachers add a location](#5-pr-254-teachers-add-a-location)
6. [Reviews I gave](#6-reviews-i-gave)
7. [How this fits the overall system](#7-how-this-fits-the-overall-system)

---

## 1. Summary

This was the Milestone 1 demo week. I finished my week 9 task, "teachers add audio and locations": teachers can now upload a clip for each difficulty and add their own rooms. Before teachers could add rooms, games had to stop picking rooms that can't be played, so I did that first.

| PR | Issue | Requirement | Size | Reviewers | Status |
|---|---|---|---|---|---|
| [#238](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/238) Default profile icon | [#237](https://github.com/COSC-499-W2026/capstone-project-team-7/issues/237) | Students without an icon still show one on the leaderboard | 6 files, +28/−10 | Gamu, `<reviewer>` | Merged Nov 18 |
| [#252](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/252) Clue audio for each difficulty | [#251](https://github.com/COSC-499-W2026/capstone-project-team-7/issues/251) | Teachers can upload the Basic, Advanced and Expert clip for a location | 8 files, +113/−34 | Gamu, `<reviewer>` | Merged Nov 22 |
| [#258](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/258) Games pick ready locations | [#255](https://github.com/COSC-499-W2026/capstone-project-team-7/issues/255) | A game never sends a student to a room it can't finish | 10 files, +163/−22 | `<reviewers>` | Merged Nov 22 |
| [#254](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/254) Teachers add a location | [#253](https://github.com/COSC-499-W2026/capstone-project-team-7/issues/253) | Teachers can add a room with a clue in their class's language | 7 files, +236/−6 | Gamu, Dan | Merged Nov 22 |


CI still can't start because of the billing lock, so the test results below are local runs, as agreed by the team in week 9.

**Claim labels.** *Observed* means I ran it or saw it (test output, review text, git history). *Generated* means AI-written code that I reviewed.

---

## 2. PR #238: Default profile icon

Frontend: `src/frontend/src/assets/default-profile-icon.svg` (new), `components/ProfileIcon.tsx`, `components/LeaderboardTable.tsx`

- [x] As part of #237 and the profile requirement, a student who hasn't equipped an icon showed an empty circle on the class leaderboard. Therefore, `ProfileIcon` now draws a plain person outline when the id is empty or unknown, and the leaderboard names it "Default profile icon" for screen readers.
- [x] I kept it frontend only. The database only lets a student equip an icon they own (#198), so storing a default would need a migration and an owned row for every student. The API still returns `profile_icon: null`.
- [x] After the first commit the icon didn't show, because the SVG's URL wasn't quoted inside `url(...)`. I fixed that in `c3ae76e`, and changed its colour to a neutral blue so it doesn't look like a store icon (`12e728b`).
- [x] Limitation: once a student equips an icon there's no way back to the default.
- [x] The PR contains small changes: `profileIconStyle` changed by 5 lines. No temporary workaround, because the default only replaces the old empty circle.
- [x] Gamu approved. It answers the question from the #198 review about what new students should show.
- [x] This work belongs in the Profile and Rewards process of the Level 1 DFD. No diagram change, because no data flow changed.

**Tests**

- [x] Positive: `a student with no equipped icon gets the default icon`, `an equipped icon replaces the default icon`, and the leaderboard test now checks a student with `profile_icon: null` shows "Default profile icon".
- [x] Negative: `an unknown id shows the default icon instead of the wrong picture`.
- [x] These are unit tests in `tests/frontend/profileIcon.test.ts` and `tests/frontend/leaderboard.test.ts`. Integration tests aren't needed because nothing outside the component changed.
- [x] This PR did not break anything else (observed): `npm test` gave 26 files, 230 tests passed; `tsc --noEmit` clean; `npm run build` succeeds. The existing tile, size and locked tests pass unchanged.

---

## 3. PR #252: Clue audio for each difficulty

Backend: `src/backend/teacher_locations.py`, `utils/audio_storage.py`. Frontend: `components/ClueAudioForm.tsx`, `api/teacherLocations.ts`

- [x] As part of #251, a teacher needs to upload the clip students hear on Advanced and Expert, not only Basic. #228 only saved Basic, so a teacher's upload during the demo wouldn't play for an Advanced game. Therefore, the upload takes an optional `difficulty` (basic, advanced or expert) and saves to the same folder the game plays that level from (Dan's #210). Without it, Basic is saved, as before.
- [x] The location list now returns `audio` with true or false for each level, in place of `has_audio`, and the form shows "Has Basic · Missing Advanced, Expert" with a Difficulty dropdown.
- [x] The difficulty is a query parameter because the body is the raw MP3, the same way game photos are sent. It's typed as the backend's `Difficulty` enum, so an unknown level is a 422 before anything is read or saved.
- [x] The form needs a Basic/Advanced/Expert list, and `AssignHuntForm` already has one. I moved both into a shared `utils/difficulties.ts` (`806c0cd`), but that touches two more files and makes the PR 10 files, so I moved the list back into the form (`2dcfad3`). Gamu flagged the same copy in review. It's a follow-up, not fixed in this PR.
- [x] Limitations:
  - The Basic/Advanced/Expert list is in two forms (above).
  - Clips are still shared by every class using a location. Gamu asked again about per-class audio. I replied that it needs a new table mapping several clips to one location, so I want the diagrams and database design worked out first.
- [x] No temporary workaround: the upload writes to the same `audio_path` the game reads, so a clip plays as soon as it's saved. `location_summary` is 3 lines and `upload_audio` is 12. Apart from the duplicated list above, I checked the diff for hardcoded values, dead code, unnecessary calls, extra conditionals, deep nesting and functions with unrelated jobs, and found none.
- [x] This work is in `teacher_locations.py` and `audio_storage.py` because that's where #202 put upload and file handling.
- [x] This work belongs in 6.2 Upload Clue Audio of the Level 2 Manage Level Content DFD. The flow is the same; the clip now goes to the chosen level's folder in D2 Clue Audio Files.

**Tests**

- [x] Positive: `test_upload_saves_the_clip_for_the_chosen_difficulty[advanced]` and `[expert]` (file in that level's folder, Basic unchanged), `test_upload_with_basic_difficulty_saves_the_basic_clip`, `test_list_shows_each_difficulty_separately`, `test_save_audio_for_a_difficulty_goes_in_its_folder`.
- [x] Negative: `test_unknown_difficulty_is_rejected_and_nothing_is_saved` (`hard` gives 422, no file written). The existing 401, 403, 404, 413, 422 and 503 tests pass unchanged.
- [x] Frontend: the upload sends `?difficulty=advanced`, and the status text names the levels a location has and is missing.
- [x] The route tests are integration tests (Postgres and a temp audio folder). `test_save_audio_...` and the frontend tests are unit tests.
- [x] Directories: `tests/backend/test_teacher_locations.py`, `tests/backend/test_audio_storage.py`, `tests/frontend/clueAudio.test.ts`.
- [x] This PR did not break anything else (observed): `pytest tests/backend` 848 passed, none skipped; `npm test` 28 files, 238 tests passed; `tsc` clean; build succeeds. Gamu also ran the backend and frontend tests for it and they passed.

---

## 4. PR #258: Games only pick ready locations

Backend: `src/backend/utils/ready_locations.py` (new), `src/backend/game_session.py`

- [x] As part of #255, once teachers can add rooms (#254), a game could pick a room with no GPS target or no clip for its level, and the student would get stuck halfway. Therefore, `ready_location_ids(connection, language, difficulty)` keeps only rooms with a clue in the language, a GPS target, and a clip for that difficulty, and `create_game` picks 5 at random from those. Fewer than 5 ready still gives 409 and no game is saved.
- [x] Clips are files, not rows, so the clip check is done on disk with the same `audio_path` the game plays from. That means "ready" can't disagree with what the game actually plays.
- [x] Before this, an Advanced or Expert game without the generated clips started fine and failed at the first clue. Now it returns 409 at the start (observed in the tests below). The README says how to get the clips locally.
- [x] Limitation: the clip check reads every candidate file each time a game starts. With our ~20 rooms that's fine. If the pool gets large, we'd store which clips exist in the database.
- [x] No temporary workaround: hunt games and normal games both use the new function, and I plan to reuse it to show teachers which rooms are missing GPS or clips, so "ready" is defined in one place. `ready_location_ids` is 10 lines.
- [x] I checked the diff for hardcoded values, duplicate code, dead code, unnecessary calls, extra conditionals, deep nesting and mixed responsibilities, and found none. The test fixtures repeated "write a clip for each room", so I added one `add_clips` helper in `test_game_session.py` that the other test files use.
- [x] It's in `utils/` because both game start and future teacher pages need it, and it isn't a route.
- [x] This work belongs in 2.3 Start or Resume Game (Get 5 Locations) of the Level 2 Play Game DFD. The diagram shows 2.3 reading only from D1. It now also checks D2 Clue Audio Files, so the diagram needs that flow added.

**Tests**

- [x] Positive: `test_game_never_picks_a_location_that_is_not_ready` (6 rooms, 1 without GPS, 5 games never pick it), `test_advanced_game_skips_a_location_with_only_a_basic_clip`, `test_basic_game_can_still_pick_a_location_with_only_a_basic_clip`.
- [x] Negative: `test_fewer_than_five_ready_locations_is_a_conflict` (4 of 5 have an Expert clip: 409, no game saved), `test_location_without_gps_is_not_ready`, `test_location_without_a_clip_for_the_difficulty_is_not_ready_for_it` (each level), `test_location_without_a_clue_in_the_language_is_not_ready`.
- [x] `test_choices_select_pool_and_are_saved` now fakes `ready_location_ids` and checks all 6 languages × 3 difficulties reach it.
- [x] `test_ready_locations.py` and the game tests are integration tests (Postgres and a temp audio folder). `test_start_game_choices.py` is a unit test.
- [x] This PR broke the existing game, quit, building hint, listens and hunt tests at first, because their rooms had no clips and so weren't ready anymore. Therefore, their fixtures now write clips with `add_clips`. Their assertions are unchanged.
- [x] Now it doesn't break anything else (observed): `pytest tests/backend` 874 passed, none skipped.

**Accidental push to `main` and how I fixed it**

All times are Nov 20, from my git reflog (observed).

- [x] What happened: #255 changes `create_game`, which Gamu's #224 adds. #224 wasn't merged yet, so at 14:53 I built my branch on top of Gamu's `224-link-games-to-assigned-hunts` branch and committed the #255 work on it. At 15:05 I pushed it, but the push went to `main` instead of my branch. That put Gamu's #224 commit (`a57c093`) and my three commits (`8cfab5a`, `7c4828c`, `fe5e302`) on `main` with no review. Because Gamu's commit was now on `main`, GitHub marked Gamu's PR #250 as merged and closed it.
- [x] Why it was a problem: unreviewed code was on `main`, including migration `015_hunt_games.sql`. Anyone who pulled and ran `migrate.py` would apply a migration that might still change in review, and `migrate.py` rejects a migration file that changes after it's applied.
- [x] How I fixed it:
  - At 15:08 I made one revert commit (`3497a6b`) on a new branch and merged it through #256 at 15:12, so the code was on `main` for about 7 minutes. I used a revert instead of a force push, so I didn't rewrite `main` under anyone who had already pulled. After the revert, `main`'s files were the same as before the push (`6b507a8`), so teammates' open branches still merged cleanly.
  - The original commits stay in `main`'s history, so reopening the old branches would have shown nothing to merge. Therefore, I cherry-picked Gamu's commit unchanged onto a new branch (`224-link-games-to-assigned-hunts-2`, opened as #257), and my three commits on top of it (`255-games-pick-ready-locations-2`, this PR). This PR says "Merge after #224" so they merge in order.
- [x] Limitation: nothing stops this happening again. A branch protection rule on `main` that requires a reviewed PR would block a direct push, but we have disabled that because of the failing CI so that we can merge PRs with failed CI.

---

## 5. PR #254: Teachers add a location

Backend: `src/backend/location_creation.py` (new), `migrations/016_location_created_by.sql` (new), `badges.py`, `main.py`

- [x] As part of #253 and the week 9 task, a teacher needs to add a room for their class's language without the seed scripts. Therefore, `POST /api/teacher/classes/{id}/locations` takes building, room, the number and description clue text, and GPS, and returns 201. If the room already exists, the clue is added to it and its GPS and owner are left as they were.
- [x] A room the OCR can't read could never be confirmed by photo, so a student would be stuck there. Therefore, the building and room must match the same `ROOM_NUMBER` pattern from `utils/ocr.py` that the photo check uses, or it's 422 "Use a campus building code and room number, like COM 316".
- [x] The room and clue are saved in one transaction. A room that already has a clue in that language is 409, and the first clue is kept.
- [x] The review by Gamu identified two problems:
  - Without required GPS, a room would never be picked (#258), and there's no way to add GPS later. Therefore, latitude and longitude are required (422 without them).
  - Teacher rooms would change badge totals. Therefore, migration 016 adds `base_game` to `location_clues`, false for teacher clues.
- [x] Dan then asked for the badge filter in this PR rather than a follow-up. Therefore, `load_progress` in `badges.py` counts only base-game clues for the total and the rooms found. Without it, a teacher adding a room would lower every student's progress towards a badge.
- [x] Limitations:
  - Backend only. The dashboard form is next.
  - A new room isn't playable until it has a clip for each level. #258 makes games skip it until then.
  - Only buildings in the OCR pattern can be added.
- [x] No temporary workaround: rooms go into the same `locations` table the seed uses. `save_location` is 12 lines, `add_location` 18 and `check_room` 4. I checked for hardcoded values (the 50 m radius is a named constant, the same as seeded rooms), duplicate code (it reuses `owned_class`, `database_unavailable` and `ROOM_NUMBER`), dead code, unnecessary calls, extra conditionals, deep nesting and mixed responsibilities, and found none.
- [x] It's a new `location_creation.py` because adding rooms is a separate job from listing and uploading audio in `teacher_locations.py`, which is already 83 lines.
- [x] This work belongs in 6.0 Manage Level Content of the Level 2 DFD. The diagram only has 6.1 View Class Locations and 6.2 Upload Clue Audio, so it needs an Add Location process that writes to D1.

**Data receipts**

- [x] `locations.created_by` references `teachers(user_id)` with `ON DELETE SET NULL`, so a room stays for every class using it if the teacher is deleted. Seeded rooms have none. It's there so only the owner can edit or retire a room later.
- [x] `location_clues.base_game` is `NOT NULL DEFAULT TRUE`, so every existing clue counts for badges and only new teacher clues are false.
- [x] Input is checked before the database: `extra="forbid"`, text trimmed, building in uppercase, latitude −90 to 90 and longitude −180 to 180 with no infinity or NaN, and no radius field.
- [x] Migration 016 skips 014 and 015 because Gamu's branches used them. Migrations run in name order, so the merge order doesn't matter.

**Tests**

- [x] Positive: `test_added_location_is_saved_with_its_gps_and_listed`, `test_building_is_saved_in_uppercase`, `test_existing_room_gets_the_clue_in_another_language`, `test_adding_a_teacher_clue_leaves_badge_progress_unchanged`.
- [x] Negative: these behaved as expected:
  - `test_location_without_gps_is_rejected` (3 cases) and `test_invalid_location_is_rejected_and_nothing_is_saved` (11 cases): 422, nothing saved
  - `test_room_with_a_clue_in_the_language_is_a_conflict`: 409, first clue kept
  - `test_other_teachers_class_is_not_found`, `test_unknown_class_is_not_found`: 404
  - `test_missing_session_and_students_are_rejected`: 401 and 403
  - `test_database_failure_returns_503`
  - `test_finding_a_teacher_added_room_does_not_count_towards_a_badge`
- [x] The route and badge tests are integration tests against Postgres. The 503 test is a unit test with a faked connection.
- [x] Directories: `tests/backend/test_location_creation.py`, `tests/backend/test_badges.py`.
- [x] This PR did not break anything else (observed): `pytest tests/backend` 878 passed, none skipped. The existing badge tests pass unchanged.

---

## 6. Reviews I gave

| PR | Author | What I found | Outcome |
|---|---|---|---|
| #240 Student details on dashboard | Gamu | No bugs. Only the signed-in student's own number is returned. The Testing section had no counts, and two tests added nothing | Approved, merged |
| #243 Building only on Basic | Gamu | The rule is right. The 3 new tests need Postgres and were skipped locally with "will run in CI", which can't run. They also copy setup `test_game_session.py` already has | Approved, merged |
| #244 Save for later or quit | Gamu | Quitting is one guarded UPDATE, and quit games are kept, which fits our keep-history rule. "Keep playing" was confusing next to Submit photo; we agreed to revisit it in Milestone 2 | Approved, merged |
| #248 Count clue listens | Gamu | The count goes up inside the database, so plays at the same moment all count. It conflicted with my #255 on merge order, so whichever merged second needed its test setup updated | Approved, merged |
| #249 My progress details | Gamu | Both queries counted quit games, there was no 503 test, and "slowest game" includes time a game was saved for later | Approved, merged |
| #261 Advanced and Expert clues | Dan | I checked all five puzzles add up to the right room, and LIB 312 and 317 now sound different. The 10 committed MP3s took it to 14 files | Approved after the MP3s were removed, merged |
| #263 Skip a location | Dan | Locks rows in the same order as answering, so no deadlock, and a stale skip is refused. Skipping must also reset `listens`, which was already on `main`. Fixed in #269 | Approved, merged |
| #265 Record clue plays on the game screen | Dan | The counting rule is right, but the branch conflicts with `main` and the player has no Vitest test | Approved after a rebase, merged |
| #267 GPS hint after five minutes | KoesOremus | The timer is kept on the server and reset in the same UPDATE as the answer and skip, so there's no race. But the hint uses a fixed 10 m radius that disagrees with the answer radius, so a student inside the answer radius can be told they're too far. It also only runs once, and has no frontend test | Approved, merged |
| #269 Debrief data for finished hunts | KoesOremus | Scoped to the signed-in student and small. It duplicates the "hardest locations" query in `student_progress.py` with different ranking rules, so students would see two different lists. Skip resets `attempts` but not `listens`, so a skipped room's plays count toward its replacement | Approved after both were fixed, merged |
| #271 Show the debrief | KoesOremus | The page is cleanly split into an API module, a view and a page. "View debrief" shows every completed hunt, not the one just finished, and Basic hunts show the description text as vocabulary even though Basic clues never say it. Stacked on #269, so it's 10 files until the backend change moves into #269 | Approved, merged |

---

## 7. How this fits the overall system

Teachers can now manage hunt content without the seed scripts. They add a room for their class's language (#254) and upload its clip for each level (#252), and games only use a room once it has GPS and a clip for the level being played (#258), so a teacher's half-finished room can never break a student's game. `base_game` keeps teacher rooms out of badges, so badge progress means the same thing for every student. The default icon (#238) means every student on the leaderboard has a picture.

Next week I plan to add the dashboard form for adding a location, show teachers which rooms aren't ready using `ready_location_ids`, share the difficulty list between the two teacher forms, and start the database design for per-class audio.
