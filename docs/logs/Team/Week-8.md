# Week 8 Team Log: Team 7

Authors: Ashish, Dan, Gamu, Madiba

October 26–November 1, 2026

## PRs covered

| PR | Author | What | Status |
|---|---|---|---|
| [#154](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/154) | Dan (danruk) | Check the student's GPS location when they submit an answer | Merged |
| [#155](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/155) | Dan (danruk) | Frontend: capture the location and send it with each game photo | Merged |
| [#160](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/160) | Gamu (gamurrrrr) | Demo: create account page with automatic login | Merged |
| [#161](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/161) | Gamu (gamurrrrr) | Language badges part 1: badge rules and saving earned badges | Merged |
| [#163](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/163) | Gamu (gamurrrrr) | Language badges part 2: badges endpoint and awarding badges during the game | Merged |
| [#165](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/165) | Gamu (gamurrrrr) | Teachers assign hunts to a class, students see their assigned hunts | Merged |
| [#167](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/167) | Ashish (nayakashish) | Stopwatch on the game screen, final time on the finish screen | Merged |
| [#169](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/169) | Ashish (nayakashish) | Clue audio moved out of the Docker image into a bind mount | Merged |
| [#171](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/171) | Ashish (nayakashish) | Students see and resume their unfinished games | Merged |
| [#173](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/173) | Madiba (KoesOremus) | Basic teacher dashboard: classes, language and join code | Merged |

## Goal and work distribution

- **Goal:** extend the demo to include points and levels, working backwards from the client demo: create an account, sign in as a student, and sign in as a teacher with a teacher dashboard. We also agreed to connect GPS to the game, which was the remaining link from last week.
- The Tuesday, October 27 meeting set the rules for this work. Points will be based on attempts, not time, because pause and resume would make time-based scoring easy to cheat. Time is tracked and shown like a stopwatch. Photo uploads and audio listens stay unlimited until we can ask the client.
- **Ashish** built the stopwatch (#167), moved clue audio out of the backend image (#169), and added resuming unfinished games (#171).
- **Gamu** built the create account page (#160), the language badges (#161, #163), and teacher-assigned hunts, which was a new idea from this week's meeting (#165). Also added the badge mockups for all six languages.
- **Dan** connected GPS to the game: the backend now checks the location with each answer (#154), and the frontend captures it and sends it with the photo (#155).
- **Madiba** built the first teacher dashboard (#173).

**Did we meet the goal?** In progress, and this log will be updated as the week continues. The demo path now works from start to finish: a new student can create an account and land on their dashboard, resume an unfinished game, and play with a stopwatch running, with GPS checked on each answer. Badges are earned while playing. A teacher can log in to a dashboard, and hunts can be assigned through the API. We are still working on points and levels this week: for now, every correct spot gives 10 points and every game is French on Basic difficulty.

## Code-base health

- **Dependent PRs.** #163 was built on #161 and targeted its branch, so CI never ran on it, because CI only runs on PRs into `main` or `dev`. We changed its target to `main` and CI then ran. #155 also includes #154's changes, and Ashish asked that #154 not be merged alone, since requiring GPS on answers before the frontend sends it would make the game unplayable. Next sprint, PRs that build on each other will still target `main`, and we will agree on the merge order in the PR.
- **Shared files.** `game_session.py` was changed by #154, #163, #167, #169 and #171, and `App.tsx` by #160, #167, #171 and #173. This caused a merge conflict between #167 and #160. These two files are becoming the place every feature touches, so we should watch their size and split them if needed.
- **Reuse.** #154 reuses the GPS validation from #134. #160 reuses the existing login function. #161 reuses the shared `Difficulty` values, and Master and Polyglot reuse the existing badge rules. #165 reuses `require_teacher`, `require_student` and each class's existing language. #167 uses the `started_at` and `finished_at` columns that `game_sessions` already had, so it needed no migration. #171 reuses the same game fields as start game, so a resumed game opens the same way as a new one.
- **Not trusting the client.** The stopwatch time comes from the backend, so a wrong phone clock can't change it (#167). Room coordinates stay on the server, and a rejected GPS reading doesn't change attempts, points or progress (#154).
- **Schema changes.** `008_student_badges.sql` (#161) and `009_assigned_hunts.sql` (#165). Assigned hunts use `ON DELETE RESTRICT`, which fits our pattern of keeping records for teachers, so a class with hunts can't be deleted. We may need a way to archive hunts later.
- **Configuration.** Clue audio now comes from a folder set by `AUDIO_DIR`, which is bind-mounted in Docker (#169). New or replaced clips no longer need an image rebuild, and this will support teachers uploading audio later. Audio paths live in one module, `utils/audio_storage.py`.
- **Known debt.** `database_unavailable` is imported from `teacher_access.py` by student code and should move to a shared file. Several tests borrow setup from `test_teacher_access.py`, which should move into a shared `conftest.py`. Resume has no click test yet. Start always makes a new game, so unfinished games can pile up. Assigned hunts aren't linked to games yet.

## Testing and validation

| Check | Environment and command | Result | Execution evidence |
|---|---|---|---|
| Full backend | Ubuntu, Python 3.13, PostgreSQL 17; `python -m pytest tests/backend` | Passed: 548 tests on `main` at `dcba6b2` | [CI backend job](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/41083923296/job/124159959304) |
| Frontend build and tests | Ubuntu, Node 22; `npm ci`, `npm run build`, `npm test` | Passed: 55 tests, 8 files on `main` at `dcba6b2` | [CI frontend job](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/41083923296/job/124159959501) |
| Full backend with badges | Same as above, on the #163 branch | Passed: 565 tests at `bff4e21` | [CI backend job](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/41103928484/job/124228040642) |

Also checked in review:

- #155: GPS flow run on a laptop with coordinates faked through devtools, by Gamu. 50 frontend tests and the build passed.
- #167: 34 game session tests and 51 frontend tests passed, including a wrong photo on the last spot not stopping the clock.
- #169: 37 audio and game tests passed. Checked with Docker that the audio isn't in the image and that all 5 French clips come through the mount.
- #171: 38 game session tests and 47 frontend tests passed. Checked by hand that finishing a game removes it from the ongoing list.
- #173: 49 frontend tests and the build passed. Browser checks covered loading, empty and error states, session expiry, and desktop and mobile layouts.

**Manual demo check:** we demoed to the TA on Thursday, October 29, and it went well. The main things to follow up on are tweaking the location check and figuring out elevation.

## Architecture and DFD alignment

This sprint adds these data flows:

1. **Signup.** The create account form sends the student's details to the existing signup endpoint, then logs in through the existing login process.
2. **GPS.** The browser captures a fresh location before each photo upload. `POST /api/game/{game_id}/answer` checks it against the current target before running OCR, so GPS, the last missing link from last week, is now connected.
3. **Badges.** After a correct answer, the backend reads the student's progress and saves any new badges to `student_badges` in the same transaction as the answer. `GET /api/student/badges` returns every badge, earned or locked.
4. **Assigned hunts.** `POST /api/teacher/classes/{class_id}/hunts` checks that the teacher owns the class, takes the class's language, and writes to `assigned_hunts`. `GET /api/student/hunts` reads the hunts for the student's classes.
5. **Game time and resume.** The clue and answer responses now carry the elapsed and final time, worked out from `game_sessions`. `GET /api/game/ongoing` lists the student's unfinished games.

New DFDs covering these flows are being generated and will be added soon.

## Collaboration process and next steps

All PRs targeted `main` and went through teammate review. Reviews caught several issues before merge:

- a confusing "Please fill in every field" message for a username or student number that was too long (#160)
- hardcoded languages, now read from the `languages` table, and a duplicated test helper (#161)
- `ON DELETE CASCADE` on assigned hunts, which would have deleted hunts with their class (#165)
- merging #154 before #155 would have made the game unplayable
- a PR touching 14 files (#167). We discussed it and kept it together, since the changes were small and needed each other

We are continuing this week on the attempts-based points system and levels with language and difficulty choice. Redeeming points (#156) depends on points, so it follows after. Also planned are the leaderboard, the class roster page (#174), the admin side of the dashboard, and keeping the OCR models in a Docker volume (#148). After the TA demo, we need to tweak the location check and figure out elevation, since it isn't accurate enough yet to tell floors apart. We also need to test GPS and OCR on a real phone on campus, link assigned hunts to games, and add a teacher screen for assigning hunts. We still need to ask the client about limits on photo uploads and audio listens.
