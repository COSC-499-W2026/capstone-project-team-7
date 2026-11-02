### Week 8: Ashish Nayak
Oct 26 to Nov 1

**Contents**

1. [Summary](#1-summary)
2. [PR #167: Stopwatch and final time](#2-pr-167-stopwatch-and-final-time)
3. [PR #171: See and resume unfinished games](#3-pr-171-see-and-resume-unfinished-games)
4. [PR #180: Join a class from the dashboard](#4-pr-180-join-a-class-from-the-dashboard)
5. [PR #182: List a student's classes](#5-pr-182-list-a-students-classes)
6. [PR #169: Move clue audio out of the backend image](#6-pr-169-move-clue-audio-out-of-the-backend-image)
7. [Reviews I gave](#7-reviews-i-gave)
8. [How this fits the overall system](#8-how-this-fits-the-overall-system)

---

## 1. Summary

This week the team's goal was to extend the demo towards the client's flow: create an account, sign in as a student, and sign in as a teacher to a dashboard. My part was on the game and student side: a stopwatch, resuming unfinished games, and connecting class joining and the class list to the student dashboard. I also moved clue audio out of the backend image, which is more of a refactor than a feature, so I put it last in this log.

| PR | Issue | Requirement | Size | Reviewers | Status |
|---|---|---|---|---|---|
| #167 Stopwatch | #166 | Show a stopwatch during a game and the total time on the finish screen | 14 files, +122/−27 | Gamu, Dan | Merged |
| #171 Resume games | #170 | Students see their unfinished games and pick up where they left off | 8 files, +238/−5 | Dan, Gamu | Merged |
| #180 Join a class | #179 | Students can self-enrol using a class code, from the dashboard | 5 files, +155/−1 | Gamu, Dan | Merged |
| #182 My classes | #181 | Students can see the classes they're enrolled in | 9 files, +144/−16 | Gamu, Dan | Merged |
| #169 Clue audio | #168 | Clue audio can be added without a code change or an image rebuild | 10 files, +66/−27 | Dan, Gamu | Merged |

#167 and #169 are over or at the 10-file guideline. I raised this on both PRs: each file has a small change, and the changes only work together. Gamu asked whether #167 could be split, and we agreed to keep it together (details below). #182 is built on #180, so #180 merged first. GitHub shows #182 as 10 files, +295/−13 because that count includes #180's changes. The size above is what #182 added at its merge commit (`0170f97`).

**Claim labels.** *Observed* means I ran it or saw it (test output, review text, CI). *Generated* means AI-written code that I reviewed.

---

## 2. PR #167: Stopwatch and final time

Backend: `src/backend/game_session.py`. Frontend: `components/Stopwatch.tsx`, `utils/formatTime.ts`, `pages/GameScreen.tsx`, `pages/FinishedScreen.tsx`, `App.tsx`

- [x] As part of #166, a student playing a game needs to see how long they've been playing, and their total time when they finish. Therefore, I added elapsed_seconds to the clue response and final_time_seconds to the answer response. The game screen shows a counting stopwatch and the finish screen shows "Time: m:ss".
- [x] Both times are worked out by the backend from started_at and finished_at, which game_sessions already has. This means there is no migration, and a wrong phone clock can't change the result. The Stopwatch component only uses the phone clock to count the time since the page loaded, and it resyncs with the backend each time the clue reloads after a photo.
- [x] final_time_seconds comes from the same UPDATE that sets finished_at, using RETURNING, so the time returned can't differ from what is saved. The value stays null until the 5th correct answer, so a wrong photo on the last spot doesn't stop the clock.
- [x] After adding the new field, a backend test failed because the fake game in test_answer_check.py didn't have final_time_seconds. Therefore, I added the field to the fake (`2e495ca`). I fixed the test data and not the route, because a real game row always has this field.
- [x] When I reviewed the generated answer.ts change, I checked what happens if a finished game comes back with a bad time. Therefore, a finished game with a missing or negative final time is treated as a bad response, the same as other invalid answers. `rejects incomplete or contradictory verification responses` covers this.
- [x] Limitations:
  - The stopwatch doesn't stop when a student leaves. The time is always now minus started_at, so a resumed game (#171) includes the time spent away. This doesn't affect scoring, because the team agreed on Oct 27 that points are based on attempts and not time. If we build pause (#150), it will need to change this.
  - The stopwatch shows on the clue screen, not the photo page.
- [x] The PR does not contain a temporary workaround because the time comes from the existing columns.
- [x] The PR contains small functions: Stopwatch is about 10 lines and formatTime is 8 lines or fewer. I can confirm the contribution does not contain any of the following:
  - hardcoded values
  - duplicate code
  - dead code
  - unnecessary function calls
  - excessive conditional logic
  - deep nesting
  - high cyclomatic complexity
  - classes/modules/functions with many unrelated responsibilities
- [x] Gamu requested a split because the PR changes 14 files (5 of them tests). I re-reviewed it and replied that the line count is small (+122/−27), the changes are thin across each file, and keeping frontend and backend together lets one run of the branch show the whole feature. I offered to split the commits into two PRs if Gamu still wanted that. Gamu agreed to keep it and approved. A limit of this choice is that the PR is still over the 10-file guideline, however to me this is justified. Dan also approved.
- [x] Before merging, updating from `main` gave conflicts with Dan's GPS work (#155) in game_session.py and test_answer_check.py. The stopwatch and GPS fields don't depend on each other, so I kept both, and the affected tests and the frontend build passed on the merge commit (`7f7bdba`).
- [x] Stopwatch.tsx is in `components/` because it's part of a page and not a page itself. formatTime.ts is in `utils/` because it's a pure helper.
- [x] This work belongs in 5.4 Present Next Location (time on each clue) and 5.10 Show Final Score (final time) of the Play Game DFD (Level 2).

**Tests**

- [x] Positive:
  - `test_clue_shows_time_since_the_game_started`: a game started 90 seconds ago gives 90–92
  - `test_fifth_correct_answer_finishes_game`: a game started 5 minutes ago gives a final time of 300–302
  - `gets the current clue and the time since the game started` and `the last correct photo returns the final time` on the frontend
- [x] Negative: these behaved as expected:
  - `test_correct_answer_moves_to_next_spot` and `test_wrong_answer_stays_on_spot_and_counts_attempts`: final_time_seconds is null
  - `test_wrong_last_photo_does_not_stop_the_clock`: final_time_seconds is null and finished_at stays empty
  - `rejects incomplete or contradictory verification responses`: a final time of null or −1 on a finished game throws
- [x] Edge: `formatTime.test.ts` covers 0, 9, 75, 3599 and 3725 seconds, plus negative and fractional input.
- [x] Directories: `tests/backend/test_game_session.py`, `tests/backend/test_answer_check.py`, `tests/frontend/`.
- [x] I also tested the functionality manually through the running docker system on my machine.
- [x] This PR did not break anything else in the system: CI passed.

---

## 3. PR #171: See and resume unfinished games

Endpoint: `GET /api/game/ongoing`. Frontend: `api/ongoingGames.ts`, `components/OngoingGames.tsx`, `pages/StudentDashboard.tsx`, `App.tsx`

- [x] As part of #170, a student who refreshes or leaves the game screen needs to get back to their game, since the frontend only kept the game id in memory and a refresh lost it. Therefore, I added `GET /api/game/ongoing`, which returns the signed-in student's unfinished games, newest first. The dashboard lists them under "Ongoing games" (e.g. "French · Basic · Spot 2 of 5"), and Resume opens the game screen at the current clue.
- [x] The route returns the same game fields as start game, so the frontend opens a resumed game the same way as a new one, and GameScreen already loads the current clue from the game id. The dashboard prop onGameStarted became onOpenGame, since it now does both.
- [x] When I reviewed the generated code, I did not find a problem with the core query. It filters by the session's student id and finished_at IS NULL, so it can't return another student's game or a finished one. I checked this with `test_ongoing_hides_finished_and_other_students_games`, against Postgres, and by hand.
- [x] Limitation, written in the PR: there is no limit on unfinished games yet, and Start always makes a new game. Gamu suggested a follow-up, such as one unfinished game per language or a quit button. I replied that I'd add a quit or forfeit option, since a limit of one per language could conflict with teacher-assigned hunts. Assigned hunts aren't linked to games yet.
- [x] The PR does not contain a temporary workaround. "Ongoing" means unfinished, using the existing finished_at column, so there is no migration.
- [x] The PR contains small functions: ongoing_games is about 13 lines and gameLabel is about 4. I can confirm the contribution does not contain any of the following:
  - hardcoded values
  - duplicate code
  - dead code
  - unnecessary function calls
  - excessive conditional logic
  - deep nesting
  - high cyclomatic complexity
  - classes/modules/functions with many unrelated responsibilities
- [x] Dan and Gamu approved, and both suggested a test that Resume opens the selected game, since the tests only checked that the button rendered. Therefore, I added `clicking resume opens the game that was picked` and `resume buttons are disabled while another game is starting` (`7586f00`).
- [x] The route is in game_session.py with the other game routes. OngoingGames.tsx started a new `components/` folder, for parts of a page that aren't pages themselves.
- [x] This work belongs in 5.4 Present Next Location of the Play Game DFD (Level 2), since a resumed game re-enters the flow there.

**Data receipts**

- [x] Access control: only the student role can read the list, and the student id always comes from the session, so a student can only see their own games. Teachers and admins get 403.

**Tests**

- [x] Positive: `test_ongoing_lists_own_unfinished_games_newest_first`: two games, newest first, exact fields, position 3 of 5. Frontend: `each ongoing game shows its language, level and progress with a resume button` and `clicking resume opens the game that was picked`.
- [x] Negative: these behaved as expected:
  - `test_ongoing_hides_finished_and_other_students_games`: list is `[]`
  - `test_ongoing_requires_student`: no session **401**, teacher **403**, admin **403**
  - `the list is hidden when there are no ongoing games`
  - `says the session ended so the app can show the login page` (401) and `shows a general message for server problems` (503)
- [x] Abnormal: `test_ongoing_database_failure_is_safe` returned **503** with no internal details.
- [x] Manual (observed): running the app, I saw my unfinished games, finished one, and the list went down by one. A screenshot is in the PR.
- [x] Directories: `tests/backend/test_game_session.py`, `tests/frontend/ongoingGames.test.ts`.
- [x] This PR did not break anything else in the system: CI passed.

---

## 4. PR #180: Join a class from the dashboard

Frontend: `src/frontend/src/api/joinClass.ts`, `components/JoinClass.tsx`, `pages/StudentDashboard.tsx`

- [x] As part of the requirement "students should be able to self-enrol into classes using the class code" (#79, frontend in #179), a student needs to type the code from their teacher and join without using the API directly. I built the endpoint in week 6 (#89), but the dashboard only had a disabled "Join a class" button. Therefore, I added a "Join a class" section that sends the code to `POST /api/student/classes/join` and shows "You joined French 101." and clears the box on success.
- [x] When I reviewed the generated joinClass(), I checked each failure against the backend's status codes. Each gets its own message: 404 "No class matches that code", 409 "You're already in this class", 422 "Please enter a valid class code", and any other failure a general message. A 401 throws the SessionEndedError from #147, so the app goes back to the login page. Gamu's review also confirmed that the messages line up with the backend.
- [x] Join is disabled while the box is empty or only spaces, and while the request is sending, so a second tap can't send it again.
- [x] Limitation: the box limits codes to 12 characters. This repeats the backend's limit, so if the code length changes, both need updating. It's the one fixed value in this PR, and the backend still validates the code.
- [x] The PR does not contain a temporary workaround because it uses the existing endpoint with no backend change.
- [x] The PR contains small functions: joinClass is about 15 lines and handleSubmit is about 15. I reused SessionEndedError. Other than the limitation above, I can confirm the contribution does not contain any of the following:
  - hardcoded values
  - duplicate code
  - dead code
  - unnecessary function calls
  - excessive conditional logic
  - deep nesting
  - high cyclomatic complexity
  - classes/modules/functions with many unrelated responsibilities
- [x] Gamu and Dan approved. Gamu also ran the tests.
- [x] This work is in new joinClass.ts and JoinClass.tsx files, following the pattern of one small file per concern in `api/` and `components/`.
- [x] This work belongs in 9.6 Add / Delete Students of the Class Management DFD (Level 2), as the student's way into the roster in D1 User Data SQL.

**Data receipts**

- [x] The code is trimmed before sending and limited to 12 characters in the box. The backend is still what validates it: JoinClassRequest trims, uppercases and rejects bad input (#89), so the frontend check is only for convenience.

**Tests**

- [x] Positive: `sends the class code to the join endpoint and returns the class`: a padded " abc123def456 " is sent trimmed. `joining shows the class name`.
- [x] Negative: these showed the right message:
  - `an unknown code says no class matches` (404)
  - `a class the student is already in says so` (409)
  - `an invalid code asks for a valid one` (422)
  - `says the session ended so the app can show the login page` (401)
  - `shows a general message for server problems` (503)
  - `the join button is disabled until a code is typed, and codes are 12 characters at most`
- [x] Not covered by automated tests: typing and clicking, because the frontend tests run without a browser. I checked these by hand against the running Docker stack (observed):
  - Join is disabled while the box is empty or only spaces
  - unknown code `NOPE` shows "No class matches that code"
  - the real code, in lowercase with spaces, shows "You joined French 101.", clears the box and saves the enrolment in class_enrollments
  - the same code again shows "You're already in this class"
  - typing stops at 12 characters
- [x] Directory: `tests/frontend/joinClass.test.ts`.
- [x] This PR did not break anything else in the system: CI passed.

---

## 5. PR #182: List a student's classes

Frontend: `src/frontend/src/api/profile.ts`, `components/MyClasses.tsx`, `components/JoinClass.tsx`, `pages/StudentDashboard.tsx`, `utils/languageName.ts`

- [x] As part of #181, a student needs to see the classes they're enrolled in, since #180 gave no way to see a class after joining. Therefore, the dashboard now shows "My classes" (e.g. "French 101 · French") above Join a class, using the existing `GET /api/student/profile` (Dan's #140). Joining a class refreshes the list, so the new class appears straight away.
- [x] When I re-reviewed my generated first draft, I found two repeats:
  - MyClasses imported the language name lookup from OngoingGames, so one component depended on another for a helper. Therefore, I moved it to a new utils/languageName.ts, which both now use.
  - The dashboard repeated the same "session ended or show the message" lines for each request. Therefore, the load, start game and logout errors now share one showError handler.
- [x] The class list starts as null and only shows once it has loaded, so a student who is in a class doesn't first see "You're not in any classes yet."
- [x] Limitation: students can't leave a class yet. It needs a backend change, because teachers must still be able to see a student who has left. Also, JoinClass keeps its own copy of the session check, since it's a separate component from the dashboard.
- [x] The PR does not contain a temporary workaround because it uses the existing profile endpoint with no backend change.
- [x] The PR contains small functions: MyClasses is about 15 lines, showError is 3 and languageName is 1. I can confirm that, within the dashboard, the contribution does not contain any of the following:
  - hardcoded values
  - duplicate code
  - dead code
  - unnecessary function calls
  - excessive conditional logic
  - deep nesting
  - high cyclomatic complexity
  - classes/modules/functions with many unrelated responsibilities
- [x] Gamu and Dan approved.
- [x] This work is in a new MyClasses.tsx and profile.ts, following the same pattern as OngoingGames.tsx and ongoingGames.ts. languageName.ts is in `utils/` because two components need it.
- [x] The class list is on the student dashboard, reading enrolled classes from D1 User Data SQL.

**Data receipts**

- [x] Access control: the profile endpoint uses the session's student, so a student can only see their own classes. The frontend sends no student id.

**Tests**

- [x] Positive: `gets the profile with the enrolled classes` and `each enrolled class shows its name and language`: two classes, "French 101 · French" and "Spanish 110 · Spanish".
- [x] Negative: these behaved as expected:
  - `a student with no classes is told so`: the message shows and there is no list
  - `shows a general message for server problems` (503)
  - `says the session ended so the app can show the login page` (401)
- [x] Not covered by automated tests: a joined class appearing straight away, because a join can't be simulated without a browser. I checked it by hand against the running Docker stack (observed): a student with no classes sees the message, joining adds the class without a refresh, and refreshing still lists it. Screenshots are in the PR.
- [x] Directory: `tests/frontend/myClasses.test.ts`.
- [x] This PR did not break anything else in the system: CI passed.

---

## 6. PR #169: Move clue audio out of the backend image

Files: `src/backend/utils/audio_storage.py`, `src/backend/game_session.py`, `src/backend/utils/generate_audio.py`, `compose.yaml`, `src/backend/.dockerignore`, `.env.example`

- [x] As part of #168, audio needs to be added or replaced without a code change or an image rebuild, and teachers will later upload their own. Before this, the clips were copied into the image, so every change needed a commit and a rebuild, and an uploaded file would be lost on the next rebuild. Therefore, the audio is now read from a folder set by AUDIO_DIR. In Docker, that folder is `src/backend/audio`, bind-mounted at `/app/audio`. Students see no change, so this is more of a refactor than a feature.
- [x] I changed one thing from the issue: it asks for a Docker volume, and I used a bind mount. I compared both before building. A named volume starts empty, hides the files inside Docker, and is wiped by `docker compose down -v`, which we often run to reset the database. A bind mount keeps the audio as a normal folder that we can check and that the generator script writes into. The code only reads AUDIO_DIR, so moving to a named volume later is a small change in `compose.yaml`.
- [x] The game route used to import the audio folder from generate_audio.py, a one-off dev script. Therefore, I added audio_storage.py, one small module that decides where audio lives. The route and the script both use it, and the teacher upload work can reuse it.
- [x] When I reviewed the generated audio_root(), I checked a blank AUDIO_DIR, because `.env.example` ships it blank. An empty value would otherwise become a path to the current folder. It uses `os.getenv("AUDIO_DIR") or DEFAULT_AUDIO_ROOT`, so blank falls back to the default, and `test_blank_audio_dir_uses_the_default` covers it.
- [x] Limitation: the issue also says the audio shouldn't be in the repo. The 5 French clips are still committed so the demo works after cloning, and the mounted folder is the one in the repo. We can remove them from git later if we decide. After pulling, the team has to run `docker compose up --build` once to pick up the mount.
- [x] The PR contains small functions: the three in audio_storage.py are one line each. I can confirm the contribution does not contain any of the following:
  - hardcoded values
  - duplicate code
  - dead code
  - unnecessary function calls
  - excessive conditional logic
  - deep nesting
  - high cyclomatic complexity
  - classes/modules/functions with many unrelated responsibilities
- [x] Dan and Gamu approved. I noted on the PR that it changes 10 files, with few changes in each, because a config refactor like this has to reach every file for the change to take effect.
- [x] This work is in a new audio_storage.py because where audio lives is part of the app, and shouldn't depend on a dev script.
- [x] This work belongs in the D2 Location Level Coordinates, Elevation and Audio Files data store of the Play Game DFD (Level 2), which provides the audio for 5.3 Start Game and 5.4 Present Next Location.

**Data receipts**

- [x] Audio files are modeled as files in a folder by language, building and room (`fr/COM-316.mp3`), with no database rows. The name uses building and room and not an id because ids differ in each database. I kept this model from before the PR. The upload work may need to add a column for the uploaded file name.

**Tests**

- [x] Positive: `test_clue_audio_plays_the_current_rooms_file`: AUDIO_DIR points at a temp folder, and the route returns 200, `audio/mpeg` and the file's bytes.
- [x] Negative: `test_missing_audio_file_is_not_found`: AUDIO_DIR points at an empty temp folder and the route returns **404** "Audio not found for this clue".
- [x] Config: `test_audio_folder_comes_from_audio_dir`, `test_without_audio_dir_audio_stays_in_the_backend` and `test_blank_audio_dir_uses_the_default`.
- [x] Manual checks with Docker (observed): `ls /app/audio` on the built image gives "No such file or directory", so audio is not in the image. With the mount, AUDIO_DIR is `/app/audio` and all 5 French clips are listed.
- [x] Directories: `tests/backend/test_audio_storage.py`, `tests/backend/test_generate_audio.py`, `tests/backend/test_game_session.py`.
- [x] This PR did not break anything else in the system: CI passed.

---

## 7. Reviews I gave

| PR | Author | What I found | Outcome |
|---|---|---|---|
| #154 GPS check on answers | Dan | Merging alone would make the game unplayable, since the frontend didn't send GPS yet. Asked that it wait for #155 | Approved |
| #155 Send GPS with photos | Dan | Ran the full 5-location hunt with GPS faked in devtools. Accuracy will likely need adjusting on a real phone | Approved |
| #160 Create account page | Gamu | A too-long username or student number showed "Please fill in every field", which is confusing. An AI review pointed this out | Requested changes, fixed, approved |
| #161 Language badges part 1 | Gamu | Hardcoded languages should come from the database, and a test helper was duplicated | Requested changes, fixed, approved |
| #163 Language badges part 2 | Gamu | No issues raised. The changes are thin and reuse existing parts | Approved |
| #165 Assign hunts | Gamu | `ON DELETE CASCADE` would delete hunts with their class. Asked for `RESTRICT`, to fit our pattern of keeping records for teachers | Requested changes, fixed, approved|
| #177 Faster backend tests | Gamu | No issues. The test suite runs much quicker | Approved |
| #184 Teacher dashboard demo | Madiba | Tested logging in as a teacher. Asked to stop hardcoding the languages, and to add screenshots. Gamu pointed to languageName.ts from #182 as a way to do this | Requested changes, fixed, approved |
| #186 Create classes demo | Madiba | Tested adding classes from the frontend. Suggested adding screenshots | Approved |

---

## 8. How this fits the overall system

#167 and #171 extend the game loop from last week: a student can now see their time as they play, and leave and return to a game without losing it. Both work out their data from game_sessions on the backend, so no migrations were needed. #180 and #182 connect the class and profile backend from earlier weeks to the student dashboard, so a student can join a class with their teacher's code and see that class in the browser. #169 separates clue audio from the code, which prepares for more languages and teacher uploads.

Next week we will look at extending the frontend for the client demo as well as adding more functionality to the system. Some items we are looking at adding is quitting/forfeiting games, assigning class hunts, getting details to the teacher dashboard etc. We will look at extending the features as well as progressing in our milestone requirements over the next couple weeks.