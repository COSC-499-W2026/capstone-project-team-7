### Week 7: Ashish Nayak
Oct 19 to Oct 25

**Contents**

1. [Summary](#1-summary)
2. [PR #108: Pick 5 random locations for a hunt](#2-pr-108-pick-5-random-locations-for-a-hunt)
3. [PR #114: Teachers view a class roster](#3-pr-114-teachers-view-a-class-roster)
4. [PR #133: Submit answer and finish screen](#4-pr-133-submit-answer-and-finish-screen)
5. [PR #147: Back to the login page when a session ends](#5-pr-147-back-to-the-login-page-when-a-session-ends)
6. [How this fits the overall system](#7-how-this-fits-the-overall-system)

---

## 1. Summary

This week the team's goal was a minimal working demo for the professor and TA: a student logs in, starts a game, hears a clue, takes a photo and moves through 5 spots to a finish screen, with OCR and GPS added in the backend. My part was the location picker that start game uses, the class roster, the last step of the demo flow (sending the photo and showing the finish screen), and fixing a bug, sending the student back to the login page when their session ends mid-game.

| PR | Issue | Requirement | Size | Reviewers | Status |
|---|---|---|---|---|---|
| #108 Location picker | #100 | The system shall randomly generate 5 locations from a pool of 15–20 options for each game session | 3 files, +72 | Gamu, Dan | Merged |
| #114 Class roster | #104 | Teachers can see the students enrolled in their class | 4 files, +135 | Gamu, Dan | Merged |
| #133 Submit answer and finish screen | #131 | Demo: a student's photo moves the game on, and the last spot shows a finish screen | 7 files, +144/−11 | Dan, Gamu | Merged |
| #147 Back to login when the session ends | #146 | When a student's session ends during a game, the login page shows instead of a dead end | 10 files, +56/−12 | Gamu, Madiba | Merged |

**Claim labels.** *Observed* means I ran it or saw it (test output, review text). *Generated* means AI-written code that I reviewed. Test counts come from running the suites locally against Docker PostgreSQL 17 with `TEST_DATABASE_URL` set, so no integration tests were skipped.

---

## 2. PR #108: Pick 5 random locations for a hunt

File: `src/backend/utils/location_picker.py`

- [x] As part of the requirement "the system shall randomly generate 5 locations from a pool of 15–20 options for each game session" (#100), starting a hunt needs exactly 5 different locations, picked at random. Therefore, I implemented pick_locations(pool) in a new location_picker.py. It returns 5 distinct locations in random order, or raises NotEnoughLocations ("A hunt needs at least 5 locations") if the pool has fewer than 5 different ones. Raising instead of returning a short list is what keeps the negative case ("never more or fewer than 5") from failing silently.
- [x] When I reviewed the generated picker, I checked what happens if a pool lists the same location twice. random.sample alone would treat the copies as different items and could put one location in a hunt twice. Therefore, the picker removes repeats first with dict.fromkeys (which keeps the order, so a seeded result stays repeatable), then samples.
- [x] I made the picker a pure function that takes the pool from the caller instead of reading the database. This way, we can hook it up so that a teacher can create custom hunts for a class, or for public hunts, the locations are picked from the full pool, based on what the caller gives.
- [x] The PR contains one function of about 6 lines plus the exception class. I can confirm the contribution does not contain any of the following:
  - hardcoded values
  - duplicate code
  - dead code
  - unnecessary function calls
  - excessive conditional logic
  - deep nesting
  - high cyclomatic complexity
  - classes/modules/functions with many unrelated responsibilities
- [x] Gamu and Dan approved.
- [x] This work is in `src/backend/utils/` because it is shared logic with no route.
- [x] This work belongs in the game session process of the DFD: it chooses which locations a new session stores.

**Tests (same PR)**

- [x] Positive: `test_picks_five_distinct_locations_from_pool[5]` and `[20]`: exactly 5, all different, all from the pool, and the pool passed in is unchanged. 5 is the smallest pool that works.
- [x] Negative: these behaved as expected:
  - `test_repeated_ids_in_pool_never_repeat_in_hunt`: 5 locations listed 3 times each still give each location once
  - `test_pool_with_fewer_than_five_distinct_locations_is_rejected`: empty, 4 locations, and 2 locations repeated 3 times all raise NotEnoughLocations (4 is one below the boundary)
- [x] Randomness: `test_each_hunt_gets_a_new_random_pick` (two hunts differ) and `test_same_seed_gives_same_locations` (repeatable with a seed). The random tests use a seeded random.Random, so they give the same result every run.
- [x] All unit tests: the picker never touches the database, so an integration test wouldn't add anything.
- [x] Directory: `tests/backend/test_location_picker.py`.
- [x] This PR did not break anything else in the system: CI passed, and the full backend run gives **385 passed** (377 on `main` + 8 new).

---

## 3. PR #114: Teachers view a class roster

Endpoint: `GET /api/teacher/classes/{class_id}/students`

- [x] As part of the requirement in #104, a teacher needs to see who is enrolled in a class they own. Therefore, I implemented the roster route in a new class_roster.py. It returns 200 with each student's id, username, first name, last name and student number, ordered by last name (ignoring case). A class with no students returns an empty list.
- [x] The issue also asks for points and levels played. Game sessions didn't exist when I started, so I built a version without points and levels, however I checked it can easily be added to my code. I opened a draft issue for adding points and levels once scoring exists.
- [x] The PR does not contain a temporary workaround. It reads the existing class_enrollments, students and users tables, so there is no schema change.
- [x] I reused teacher_connection for the session and role check and owned_class for ownership, so the route adds no new auth SQL. I can confirm the contribution does not contain any of the following:
  - hardcoded values
  - duplicate code
  - dead code
  - unnecessary function calls
  - excessive conditional logic
  - deep nesting
  - high cyclomatic complexity
  - classes/modules/functions with many unrelated responsibilities
- [x] Gamu and Dan approved.
- [x] This work is in a new class_roster.py because reading a roster is its own feature area, and class_enrollment.py is about changing one.
- [x] This work belongs in 9.6 Add / Delete Students of the Class Management DFD (Level 2), as the read side of the roster in D1 User Data SQL.

**Data receipts**

- [x] Privacy: no email or password hash is returned. A missing class and another teacher's class both return 404 "Class not found", so a teacher can't tell whether another teacher's class exists. Students and admins get 403 "Teacher access required" with no student data, matching the other teacher routes.

**Tests (same PR)**

- [x] Positive: `test_teacher_lists_enrolled_students` passed: exact body for both students in last-name order, and a student in another teacher's class is not included.
- [x] Negative: these failed as expected:
  - `test_requires_teacher`: no session **401**, student **403**, admin **403**, body is only the error message (the requirement's negative case)
  - `test_missing_or_unowned_class_is_hidden`: **404** "Class not found" for both
  - `test_invalid_class_id_is_rejected`: **422**
- [x] Edge: `test_class_without_students_returns_empty_list`: 200 with `[]`.
- [x] Abnormal: `test_session_check_database_failure_is_safe` and `test_roster_database_failure_is_safe` returned **503** "Database unavailable" with no internal details.
- [x] Unit: the two 503 tests.
- [x] Directory: `tests/backend/test_class_roster.py`.
- [x] This PR did not break anything else in the system: CI passed, and the full backend run gives **386 passed** (377 on `main` + 9 new).

---

## 4. PR #133: Submit answer and finish screen

Frontend: `src/frontend/src/api/answer.ts`, `src/frontend/src/pages/FinishedScreen.tsx`, `App.tsx`, `GameScreen.tsx`, `PhotoSubmitPage.tsx`

- [x] As part of the demo task #131, the photo page needed to actually send the photo, and the game needed an end. Therefore, I added submitAnswer() in answer.ts, which posts the photo to Gamu's `POST /api/game/{game_id}/answer` (#129). A correct photo goes back to the game screen with "Correct! On to the next spot." and the next clue; a wrong one shows "Not quite, try again."; after the last spot, FinishedScreen shows "You finished! You found all 5 spots." with a Back to dashboard button.
- [x] When I re-reviewed my generated first draft, I found that Submit stayed enabled while the photo uploaded. On campus Wi-Fi a few-MB photo can take seconds, and a second tap would send it again: an extra attempt for a wrong photo, or "This spot was already answered" shown instead of "Correct!". Therefore, I made changes so PhotoSubmitPage now shows "Sending..." and disables Submit, Retake and Close while the request is running.
- [x] The photo is sent as the raw request body, not FormData, because that is what the backend reads. I checked the request and the response fields (correct, attempts, finished, next_position) against the backend branch.
- [x] Moving to the next spot needs no extra state: closing the photo page remounts GameScreen, which loads the new clue itself. Back to dashboard clears the game, photo and message so a new game starts clean.
- [x] Limitations, written in the PR:
  - The backend accepts every photo until the OCR and GPS checks are connected, so "Not quite" can't be seen in a real run yet.
  - "Please log in again" doesn't open the login page; the student has to refresh. The clue and start game requests have the same gap, so all three will be fixed together in #146 (done in #147, below).
  - A failed upload doesn't keep the photo, so the student has to retake it. Madiba's #145 fixed this when it was built on top of this PR.
- [x] I followed the existing patterns and can confirm the contribution does not contain any of the following:
  - hardcoded values
  - duplicate code
  - dead code
  - unnecessary function calls
  - excessive conditional logic
  - deep nesting
  - high cyclomatic complexity
  - classes/modules/functions with many unrelated responsibilities
- [x] Dan approved. Gamu requested a change: on a 401 the student sees "Please log in again" but stays on the game screen with no way to log in. I checked, and the same gap is in the start game and clue requests, because each `api/` file turns a 401 into a plain error and nothing clears the login state. So I replied on the PR and opened #146 to fix all three together in a separate PR, using the same path the logout button already uses to return to the login page. Gamu then approved.
- [x] The PR was stacked on Gamu's login, dashboard, game screen and photo page PRs. So I ensured those merged before mine did.

**Tests (same PR)**

- [x] Positive: `sends the photo for the current spot and returns the result`: checks the URL, POST, `Content-Type: image/jpeg`, the photo as the body, and the returned result.
- [x] Negative: these showed the right message:
  - `asks to log in again when the session ended`: 401 shows "Please log in again"
  - `shows the backend's message for problems like a photo that is too large`: 413 shows "Photo is too large"
  - `shows a general message when the server gives no details`: 503 with no body shows "Could not send your photo"
- [x] `the close button is disabled while a photo is sending` in `tests/frontend/PhotoSubmitPage.test.ts`.
- [x] `cd src/frontend && npm test` gives **31 passed** (7 files), and `npm run build` passes. CI passed on the PR.

---

## 5. PR #147: Back to the login page when a session ends

Frontend: `src/frontend/src/api/sessionEnded.ts`, `api/game.ts`, `api/clue.ts`, `api/answer.ts`, `App.tsx`, `GameScreen.tsx`, `StudentDashboard.tsx`

- [x] As part of #146 (from Gamu's review of #133), a student whose session ended mid-game (it expired, or they logged out in another tab) saw "Please log in again" with no way to log in, until they refreshed. Starting a game, loading a clue and submitting a photo all had this gap. Therefore, I added a SessionEndedError in a new sessionEnded.ts. game.ts, clue.ts and answer.ts throw it on a 401, and the app returns to the login page instead of showing the message. After logging in again, the student lands on the dashboard with no old game showing.
- [x] I used an error type instead of checking the message text, so changing the wording later can't break the redirect, and only a real 401 logs the student out. A "Game not found" or "Photo is too large" still shows its message as before.
- [x] App.tsx has one sessionEnded handler that clears the game, the photo page, the last message and the finished state, then shows the login page. It is wrapped in useCallback so it stays the same function, otherwise GameScreen would load the clue again every time the app re-renders. The dashboard reuses the existing logout path, which already shows the login page, so it needed no new prop.
- [x] Limitations, written in the PR:
  - The login page doesn't say why the student was sent back. A short "Your session ended" message could be added later if we decide.
  - The redirect itself isn't covered by automated tests (see below).
- [x] I followed the existing pattern of one small file per concern in `api/`. I can confirm the contribution does not contain any of the following:
  - hardcoded values
  - duplicate code
  - dead code
  - unnecessary function calls
  - excessive conditional logic
  - deep nesting
  - high cyclomatic complexity
  - classes/modules/functions with many unrelated responsibilities
- [x] This work belongs in the login and game session processes of the DFD: an ended session sends the student back to login instead of continuing the game loop.

**Tests (same PR)**

- [x] Positive: the 401 tests for start game, the clue and the photo submit now check that a `SessionEndedError` is thrown, with "Please log in again" as its message.
- [x] Negative: `start game shows a general message for server problems` (503), `says when the game does not exist or is not yours` (404) and `shows the backend's message for problems like a photo that is too large` (413) still show their message and are checked not to be a `SessionEndedError`, so they don't log the student out.
- [x] Not covered by tests: the redirect in App, GameScreen and StudentDashboard. Testing components needs `@testing-library/react`, which isn't a dependency. I checked it by hand on `localhost`: start a game, delete the session cookie in DevTools, then press Start game or reload the clue. The login page shows, and logging in again shows the dashboard.
- [x] `cd src/frontend && npm test` gives **31 passed** (7 files), and `npm run build` passes. CI passed on the PR.

---

## 6. How this fits the overall system

The picker (#108) is the first step of a game: start game passes it the locations with a clue in the game's language and saves the 5 it returns. #133 is the last step of the demo flow: login, dashboard, start game, clue audio, camera, answer, next spot, finish. With #143 and #145 on top of it, the full demo runs end to end on `main` with real OCR checks and points. #147 covers the case where the session ends in the middle of that flow. The roster (#114) is the read side of class management. It can now grow to include points, since #143 stores them on `game_sessions`.

Next week we will look into connecting more backend to the frontend, and adding more game features to fit the app closer to the DFDs we designed.