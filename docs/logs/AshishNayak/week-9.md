### Week 9: Ashish Nayak
Nov 2 to Nov 8

**Contents**

1. [Summary](#1-summary)
2. [PR #198: Store and equip profile icons](#2-pr-198-store-and-equip-profile-icons)
3. [PR #200: Profile icon art and demo seed](#3-pr-200-profile-icon-art-and-demo-seed)
4. [PR #202: Teachers view locations and upload clue audio](#4-pr-202-teachers-view-locations-and-upload-clue-audio)
5. [DFD and architecture updates (#193)](#5-dfd-and-architecture-updates-193)
6. [Reviews I gave](#6-reviews-i-gave)
7. [How this fits the overall system](#7-how-this-fits-the-overall-system)

---

## 1. Summary

At the Nov 3 meeting we split the remaining Milestone 1 tasks for the demo after reading break. My two tasks were profile icons, which Gamu's store depends on, and letting teachers add audio and locations, teacher version first. I finished icons in two PRs and the first part of the audio task. I also updated our DFDs and system architecture diagram to match what's built, using the feedback from our earlier logs.

| PR | Issue | Requirement | Size | Reviewers | Status |
|---|---|---|---|---|---|
| #198 Profile icons backend | #197 | Students can equip a profile icon they own, and it shows on their profile | 9 files, +288/−4 | Gamu, Dan | Merged |
| #200 Icon art and demo seed | #199 | Icons can be drawn anywhere in the app, and a student can be given icons for testing | 5 files, +153/−0 | Gamu, Dan | Merged |
| #202 Teacher clue audio | #201 | Teachers can see the locations in their class's language and upload clue audio | 8 files, +325/−10 | Gamu, Madiba | Merged |
| #193 DFDs and architecture (my commits, in Gamu's docs PR) | n/a | Diagrams match the built system | 7 diagrams and README | Dan | Merged |

#200 is built on #198, so #198 merged first. GitHub shows #200 as 14 files, +441/−4 because that count includes #198. The size above is what #200 added on top of it (`91625fd` and `92c2cb5`). #202 is over our 200-line target. About 180 of its lines are tests, and it's still under 10 files and 500 lines.

CI hasn't run for us this week, so we had a discussion as a team and decided to override the CI check for this week, making sure our tests pass locally. We also decided that if a test fails when the CI runs again we would fix it as soon as we can. The test results below are local runs.

**Claim labels.** *Observed* means I ran it or saw it (test output, review text). *Generated* means AI-written code that I reviewed.

---

## 2. PR #198: Store and equip profile icons

Backend: `src/backend/profile_icons.py`, `src/backend/student_icons.py`, `src/backend/student_profile.py`, `src/backend/migrations/010_profile_icons.sql`

- [x] As part of #197 and the profile requirement, a student needs to own profile icons, pick one of them, and have it show on their profile. Therefore, I added `GET /api/student/icons`, which lists every icon with whether the student owns it and has it equipped, and `PUT /api/student/profile/icon`, which equips an owned icon. `GET /api/student/profile` now returns the equipped icon's id instead of always null.
- [x] The icon list lives in `PROFILE_ICONS` in profile_icons.py, the same way badges are listed in badges.py. Adding an icon is one line and needs no migration, because the database only stores icon ids. For Milestone 1 it has the three French icons: Croissant Cutie, Mac the Macaron and Speedy Escargot.
- [x] When I reviewed the generated equip route, I checked what happens if a student equips an icon they don't own. Checking ownership first and then updating would leave a gap between the two queries. Therefore, the ownership check and the update are one statement (`UPDATE ... WHERE EXISTS`), so an unowned or unknown icon leaves the previous icon equipped.
- [x] The database also enforces it: a foreign key from (students.user_id, students.equipped_icon_id) to student_icons means a student can't have an icon equipped that they don't own, even through a direct update. `test_database_refuses_an_unowned_equipped_icon` checks this.
- [x] Errors: an unowned icon returns **403** "You don't own this profile icon", and an unknown id returns **404** "Profile icon not found" without touching the database. Bad input returns 422, no session returns 401, teachers and admins get 403, and a database failure returns 503 "Database unavailable".
- [x] Limitations:
  - There's no way to get icons yet in this PR. Redeeming points is Gamu's #205, which only has to add rows to student_icons.
  - There's no unequip. Gamu suggested showing a placeholder when nothing is equipped. I replied that I'd planned a default icon for new accounts, and we'll decide that in a later PR.
- [x] The PR does not contain a temporary workaround, because ownership is a real table that redeeming writes to, not a hard-coded list.
- [x] The PR contains small functions: list_icons and equip_icon are about 12 lines each, and each route is under 10 lines. I can confirm the contribution does not contain any of the following:
  - hardcoded values
  - duplicate code
  - dead code
  - unnecessary function calls
  - excessive conditional logic
  - deep nesting
  - high cyclomatic complexity
  - classes/modules/functions with many unrelated responsibilities
- [x] Gamu and Dan approved. Gamu asked whether new students should get a free default icon or the frontend should show a placeholder, which is noted above for the follow-up. Gamu also noted the database doesn't check that an icon id is real, and said the redeem endpoint (#156) would check it before saving.
- [x] The queries are in profile_icons.py and the routes in student_icons.py, so the store (#205) could reuse list_icons without importing a router. The store does reuse it.
- [x] This work belongs in 7.0 Profile and Rewards (Equip Icon) of the Level 1 DFD.

**Data receipts**

- [x] student_icons has one row per icon a student owns, with the primary key (student_id, icon_id), so an icon can't be owned twice. Rows are deleted with the student (`ON DELETE CASCADE`), because icons are personal rewards and not class records.
- [x] students.equipped_icon_id is null when nothing is equipped. The composite foreign key above checks ownership in the database itself.
- [x] The icon id is validated before the database: it must be text up to 50 characters, with no extra fields (`extra="forbid"`), and it must be in `PROFILE_ICONS`.

**Tests**

- [x] Positive: `test_equip_owned_icon_is_saved_and_returned_by_profile`: 200, the database row is updated and the profile returns the icon. `test_switching_between_owned_icons_keeps_the_latest` and `test_list_marks_owned_and_equipped` also pass.
- [x] Negative: these behaved as expected:
  - `test_equipping_unowned_icon_keeps_the_previous_one`: 403, and the previous icon is still equipped
  - `test_equipping_unknown_icon_keeps_the_previous_one` and `test_unknown_icon_never_reaches_the_database`: 404
  - `test_student_with_no_icons_cannot_equip` and `test_one_students_icons_do_not_affect_another`
  - `test_bad_body_is_rejected`: missing, null, a number, 51 characters, an extra field
  - `test_requires_login`, `test_non_students_are_forbidden` and `test_database_failure_is_safe`, on both routes
- [x] `test_database_refuses_an_unowned_equipped_icon` and `test_deleting_a_student_with_an_equipped_icon_works` check the schema directly.
- [x] Integration tests (real Postgres with `TEST_DATABASE_URL` and a real login) cover equipping, listing and the schema. The bad input, login, role and database failure tests are unit tests that fake the session or the connection.
- [x] Directories: `tests/backend/test_student_icons.py`, `tests/backend/test_student_profile.py`.
- [x] I tested it by hand against the running backend: equipping before and after owning, an unowned icon, an unknown icon and no login.
- [x] This PR did not break anything else in the system: `python -m pytest tests/backend` gave 700 passed, none skipped. CI couldn't run (billing lock).

---

## 3. PR #200: Profile icon art and demo seed

Frontend: `src/frontend/src/components/ProfileIcon.tsx`, `src/frontend/src/assets/profile-icons.png`. Backend: `src/backend/utils/seed_student_icons.py`

- [x] As part of #199, the store and the leaderboard need to show icons, and we need a way to give a student icons before redeeming works. Therefore, I added one image with all 18 icons from our mockups (a transparent background, 200×200 tiles, one row per language) and a ProfileIcon component that draws any icon by id at any size.
- [x] The component uses percentages for the background size and position, so the same image works small on a leaderboard and large in the store. An optional locked look is grey and faded, matching the badges page. An unknown id shows a plain circle instead of the wrong picture.
- [x] The seed script gives a student Croissant Cutie and Mac the Macaron by email. Speedy Escargot stays locked, so the 403 can be tried. It's safe to run more than once (`ON CONFLICT DO NOTHING`), and an email with no student changes nothing.
- [x] The review by Gamu pointed out that the 50 and 20 in backgroundPosition only work for a 3×6 grid, so more icons per language or another language would point at the wrong picture. Therefore, the position is now worked out from the size of the `SHEET` grid (`92c2cb5`), and I added a test for a middle tile.
- [x] Limitations:
  - The image is cut from the mockup, about 180 px across, so it's a little soft at very large sizes. Original exports would fix that.
  - Only the 3 French icons are in the backend list so far. The others are in the image and can be added one line at a time.
- [x] The PR does not contain a temporary workaround in the app itself. The seed script is a dev tool only, and it stays useful for testing even now that redeeming exists.
- [x] The PR contains small functions: profileIconStyle is about 20 lines and seed_student_icons is about 15. I can confirm the contribution does not contain any of the following:
  - hardcoded values
  - duplicate code
  - dead code
  - unnecessary function calls
  - excessive conditional logic
  - deep nesting
  - high cyclomatic complexity
  - classes/modules/functions with many unrelated responsibilities
- [x] Gamu requested the grid change above, then approved. Dan approved.
- [x] ProfileIcon.tsx is in `components/` because it's part of a page and not a page itself. The seed is in `utils/` with our other seed scripts.
- [x] This work belongs in 7.0 Profile and Rewards (View Profile, Equip Icon) of the Level 1 DFD. Gamu's store (#206) now uses ProfileIcon for its icon grid.

**Data receipts**

- [x] The seed only inserts student_icons rows for an existing student account. The email is trimmed and compared case-insensitively, and a teacher's email matches no student, so nothing is written.

**Tests**

- [x] Positive: `finds an icon in the first tile`, `finds an icon in the last tile`, `finds an icon in a middle tile` and `keeps the same tile at a different size`. `test_seed_gives_the_demo_icons_and_is_safe_to_repeat`.
- [x] Negative: `an unknown id shows a plain circle instead of the wrong picture`, `test_seed_changes_nothing_for_an_unknown_student` and `test_seed_rejects_a_teacher_email` (no rows).
- [x] Also: `owned icons keep their colour and locked ones are grey` and `the icon is named for screen readers`.
- [x] The ProfileIcon tests are unit tests. The seed tests are integration tests against Postgres.
- [x] Directories: `tests/frontend/profileIcon.test.ts`, `tests/backend/test_seed_student_icons.py`.
- [x] I checked every icon by eye in the browser, at a large and a small size.
- [x] This PR did not break anything else in the system: 703 backend tests and 128 frontend tests passed, and `npx tsc --noEmit` was clean. CI couldn't run (billing lock).

---

## 4. PR #202: Teachers view locations and upload clue audio

Backend: `src/backend/teacher_locations.py`, `src/backend/utils/audio_storage.py`, `src/backend/utils/request_body.py`, `src/backend/game_session.py`

- [x] As part of #201 and the Nov 3 task "Teachers add audio and locations", a teacher needs to see the locations in their class's language, see which ones have audio, and upload an MP3 for one. Therefore, I added `GET /api/teacher/classes/{class_id}/locations`, which lists those locations with has_audio, and `PUT /api/teacher/classes/{class_id}/locations/{location_id}/audio`, which adds or replaces a location's clip.
- [x] I planned this as the first step of teachers managing hunt content: a location list every later step needs, with no change to the game. Adding locations, editing them and choosing locations for a hunt come next.
- [x] The upload is sent as the raw request body, the same way game photos are, so it needs no new dependency for multipart forms. Photos already had code to read the body with a size limit, so I moved it into a shared read_limited_body helper (`54b27ba`) and both routes use it. The photo route behaves the same as before.
- [x] When I reviewed the generated upload code, I checked what happens to the existing clip if an upload fails halfway. Writing straight over the file would leave a broken clip. Therefore, save_audio writes to a temp file and then swaps it in, so a failed or rejected upload leaves the old clip playing.
- [x] I also checked that the file is really an MP3. A file extension or content type can be anything, so is_mp3 looks for a valid MPEG Layer III frame header at the start of the audio, skipping any ID3 tag. I checked the 5 existing French clips have that header.
- [x] When I reviewed the generated route, a database connection would have stayed open while a slow upload streamed in. Therefore, the upload route checks access with a short connection and closes it before saving the file.
- [x] When I reviewed the generated MP3 test, one "reserved version" example was really a valid MPEG 2.5 header. Therefore, I changed it to the actual reserved bits (`ffeb`).
- [x] Errors: another teacher's class returns **404** "Class not found", the same as the roster. An unknown location, or one with no clue in the class's language, returns 404 "Location not found". A file that isn't an MP3 returns **422** "Please upload an MP3 file", over 5 MB returns 413, no session returns 401, non-teachers get 403, and a database or file failure returns 503.
- [x] Limitations:
  - Uploads are Basic only for now. Dan's #209 gives audio a difficulty, so a small follow-up will add a difficulty to the upload.
  - Locations are shared, so an upload replaces the clip for every class using that location. Per-class audio is a follow-up (see the review below).
  - Docker mounts `src/backend/audio`, which is tracked in git, so replacing a seeded clip locally shows as a changed file.
  - Clip names come from building and room, so the add-location PR must reject characters like `/`.
  - There's no form yet. I haven't tried it by hand in the browser, and the form PR will do that.
- [x] The PR does not contain a temporary workaround, because the upload uses the same audio_path the game reads, so a clip plays as soon as it's saved.
- [x] The PR contains small functions: is_mp3 and save_audio are about 10 lines each, and each route is under 15 lines. I can confirm the contribution does not contain any of the following:
  - hardcoded values
  - duplicate code (the body reader is now shared)
  - dead code
  - unnecessary function calls
  - excessive conditional logic
  - deep nesting
  - high cyclomatic complexity
  - classes/modules/functions with many unrelated responsibilities
- [x] The review by Gamu asked that uploads only apply to the teacher's own class, saved in a per-class folder. I replied that audio is global and not linked to a class in the database, so per-class audio fits better in a later PR, once difficulty audio and audio management are built up more. I also considered making the endpoint add-only so teachers couldn't overwrite existing audio. I didn't, because it would be a temporary change that only affects our dev work until per-class audio replaces it. Madiba approved with the same reasoning, and asked that per-class audio be tracked so it's done before the teacher upload is fully in the frontend.
- [x] Before merging, updating from `main` gave conflicts with Dan's #209 in audio_storage.py and test_audio_storage.py, because both changed the audio path code. I kept Dan's audio_path with its difficulty and added is_mp3 and save_audio below it (`e9e75ec`). Uploads still save as Basic. All 809 backend tests passed on the merge (observed).
- [x] The routes are in a new teacher_locations.py because it's a new teacher feature area. File handling is in audio_storage.py with the existing audio path code. The body reader is in `utils/` because both the game and teachers use it.
- [x] This work belongs in 11.0 Manage Level Content (11.2 Upload Audio Files) of the Level 2 DFD. It writes to the D2 Location Level Coordinates and Audio Files store, which 5.4 Present Next Location in the Play Game DFD reads from.

**Data receipts**

- [x] No schema change. Clips stay files named by language, building and room. has_audio is worked out from whether the file exists, so it can't disagree with what the game plays.
- [x] Uploads are checked before saving: the teacher must own the class, the location must have a clue in the class's language, and the bytes must be a real MP3 of at most 5 MB.

**Tests**

- [x] Positive: `test_upload_adds_a_clip_and_marks_the_location`: 200, has_audio is true, and the bytes are saved at the path the game reads. `test_list_shows_class_language_locations_and_audio_status` and `test_upload_replaces_an_existing_clip` also pass.
- [x] Negative: these behaved as expected:
  - `test_invalid_upload_keeps_the_existing_clip`: not an MP3, and an empty file, both give 422 and the old clip is unchanged
  - `test_too_large_upload_is_rejected`: 413, nothing saved
  - `test_other_teachers_class_is_not_found` and `test_unknown_location_or_other_language_is_not_found`
  - `test_missing_session_is_rejected`, `test_students_are_forbidden`, `test_database_failure_returns_503` and `test_failed_save_returns_503_and_keeps_the_clip`
- [x] MP3 checks: `test_mp3_with_or_without_id3_tag_is_accepted` and `test_other_data_is_not_an_mp3` (text, a cut-off header, an ID3 tag with no audio, Layer II, reserved bits, invalid bitrate). `test_save_audio_replaces_the_clip_and_leaves_no_temp_file`.
- [x] The route tests are integration tests (Postgres and a temp audio folder). The MP3 and save tests are unit tests.
- [x] Directories: `tests/backend/test_teacher_locations.py`, `tests/backend/test_audio_storage.py`.
- [x] This PR did not break anything else in the system (observed): 698 backend tests passed, none skipped, against a fresh Postgres 17 database with migrations applied, the same way CI sets it up. The photo route tests passed with the shared reader. CI couldn't run (billing lock).

---

## 5. DFD and architecture updates (#193)

These are docs, not code, so there are no tests. My 9 commits are in the docs branch, which Gamu merged with the Nov 3 minutes in #193. On #193 I listed every change in a comment so the team could check them, and asked them to say if they found errors or things to add.

- [x] Our earlier log feedback said the diagrams didn't match the system. Therefore, I updated the existing diagrams instead of redrawing them, and kept the process numbers so earlier logs still line up.
- [x] **Level 0 DFD** (`f6eaa18`): replaced the OCR API with Gmail SMTP, because PaddleOCR runs inside the backend and password resets send email. I removed the Chatbot API and updated the flow labels.
- [x] **Level 1 DFD** (`fc4ea39`): dashboard flows now carry data both ways instead of navigation, and users get data back. I added joining a class and game progress flows, and replaced the OCR API with Gmail SMTP.
- [x] **Auth DFD** (`ef113c2`): added Gmail SMTP, saving the reset token, and returning the session cookie and account status.
- [x] **Game DFD** (`11f7457`, `637afb9`): GPS is now checked before the photo, matching the code. I removed elevation and the external PaddleOCR box, and added resuming a game and the stopwatch. The first commit uploaded the wrong picture, so the second replaces it with the correct one.
- [x] **Class DFD** (`17a73f5`): added joining by code and viewing assigned hunts, and renamed class levels to hunts and student details to roster.
- [x] **User DFD** (`a97b7cb`): Add Teacher is now Approve Teacher Email, and I added a process for managing accounts and classes.
- [x] **System architecture** (`5281f5d`): replaced JWT with session cookies, and named PaddleOCR and Gmail SMTP.
- [x] **README** (`40eb67d`): updated the architecture section, removed the chatbot, and separated the Level 1 and Level 2 DFD sections.
- [x] Dan approved #193.

---

## 6. Reviews I gave

| PR | Author | What I found | Outcome |
|---|---|---|---|
| #194 Badges page | Gamu | No issues raised | Approved |
| #196 Assign hunt form | Gamu | Switching class left the old class's roster on the page, which I showed with a screenshot. Both components used the same key, so a teacher could remove a student from the wrong class. I suggested one key per component | Requested changes, fixed, approved |
| #204 Assigned hunts list | Gamu | CI still failed, so I suggested we override it this week until the problem is resolved. Hunts are deleted for real. That's probably what we want, but we should decide what gets permanently deleted and what gets archived | Approved |
| #205 Redeem icons with points | Gamu | No issues raised | Approved |
| #206 Store page | Gamu | The store works as I expect | Approved |
| #209 Difficulty clue audio | Dan | Agreed with Gamu's notes. We need a process for sharing audio, and for making sure the audio is built correctly and isn't too similar across difficulties. I generated the Advanced and Expert clips with the script (15 clips) | Approved |
| #210 Serve audio by difficulty | Dan | Well tested, small and direct, and reuses existing components | Approved |
| #212 Choose language and difficulty | Dan | Gamu asked for a split because the first version was 10 files. After Dan made it backend only, I approved the smaller PR | Approved |
| #215 Start game frontend | Dan | The frontend half of #212. Splitting it out kept both PRs small | Approved |
| #217 Class leaderboard API | Madiba | The code is minimal and the tests passed for me. It needed conflicts with `main` resolved before merging | Approved |
| #219 Class leaderboard screen | Madiba | A stray `main` from a merge broke the student dashboard, and `tsc` threw an error. I left an inline comment and approved on the condition it's fixed | Approved, with one fix |
| #221 Admin dashboard | Madiba | No issues raised. I suggested a follow-up so admins can reassign a class by its class code, not only its UUID | Approved |

---

## 7. How this fits the overall system

#198 and #200 build the profile icon part of rewards: students own icons in the database, can equip one, and the frontend can draw any icon. Gamu's redeem endpoint (#205) and store page (#206) build straight on top, so students can now earn points in games, spend them on icons and equip them. Madiba's class leaderboard (#217, #219) returns each student's equipped icon and draws it with ProfileIcon, so classmates see the icons next to their points. #202 starts the teacher side of game content. Teachers can see their class's locations and upload clue audio into the same folder the game plays from. Dan's difficulty work (#209, #210, #212, #215) means students can now choose a language and level, which the audio upload will follow next. The DFD updates make the diagrams match all of this, so the team and markers can trace each feature to its process.

Next week is reading break, and the Milestone 1 demo is after it. I plan to finish teachers adding audio and locations (the upload form, a difficulty on uploads, and adding locations), and to work through my refactoring list.
