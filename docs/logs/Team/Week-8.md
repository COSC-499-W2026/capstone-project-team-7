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
| [#177](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/177) | Gamu (gamurrrrr) | Faster backend tests and CI: quicker password hashing in tests only, cached pip installs | Merged |
| [#178](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/178) | Dan (danruk) | Points for a correct spot based on game difficulty | Merged |
| [#180](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/180) | Ashish (nayakashish) | Frontend: join a class with a class code from the student dashboard | Merged |
| [#182](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/182) | Ashish (nayakashish) | Frontend: list the student's enrolled classes on the dashboard | Merged |
| [#184](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/184) | Madiba (KoesOremus) | Basic teacher dashboard: classes, language and join code | Merged |
| [#186](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/186) | Madiba (KoesOremus) | Teachers create a class from their dashboard | Merged |

## Goal and work distribution

- **Goal:** extend the demo to include points and levels, working backwards from the client demo: create an account, sign in as a student, and sign in as a teacher with a teacher dashboard. We also agreed to connect GPS to the game, which was the remaining link from last week.
- The Tuesday, October 27 meeting set the rules for this work. Points will be based on attempts, not time, because pause and resume would make time-based scoring easy to cheat. Time is tracked and shown like a stopwatch. Photo uploads and audio listens stay unlimited until we can ask the client.
- **Ashish** built the stopwatch (#167), moved clue audio out of the backend image (#169), added resuming unfinished games (#171), and connected classes to the student dashboard: joining a class with a code (#180) and listing the student's classes (#182).
- **Gamu** built the create account page (#160), the language badges (#161, #163), and teacher-assigned hunts, which was a new idea from this week's meeting (#165). She also sped up the backend tests and CI (#177).
- **Dan** connected GPS to the game: the backend now checks the location with each answer (#154), and the frontend captures it and sends it with the photo (#155). He also made points depend on the game's difficulty and the number of photo attempts (#178).
- **Madiba** built the teacher dashboard (#184) and the form for teachers to create a class (#186). Her first version of the dashboard (#173) was more styled than the minimal demo we agreed on, so she rebuilt it as #184 to match the student screens.

**Did we meet the goal?** Mostly. The demo path now works from start to finish: a new student can create an account, join a class with a code, see their classes on the dashboard, resume an unfinished game, and play with a stopwatch running, with GPS checked on each answer. Badges are earned while playing. A teacher can log in, see their classes with each join code, and create a new class. Points now depend on difficulty (Basic 10, Advanced 20, Expert 30 for a correct spot on the first try) and on attempts: a second try earns fewer points, and a third try or later earns a fixed minimum. What is still missing is levels, since every game still starts as French on Basic difficulty. That carries over to next week.

## Code-base health

- **Dependent PRs.** #163 was built on #161 and targeted its branch, so CI never ran on it, because CI only runs on PRs into `main` or `dev`. We changed its target to `main` and CI then ran. #155 also includes #154's changes, and Ashish asked that #154 not be merged alone, since requiring GPS on answers before the frontend sends it would make the game unplayable. The same pattern showed up again later in the week: #182 includes #180, and #186 includes #184. Including the earlier PR pushed #182 to 10 files, over our limit, until #180 merges and the branch is updated. Next sprint, PRs that build on each other will still target `main`, and we will agree on the merge order in the PR.
- **Shared files.** `game_session.py` was changed by #154, #163, #167, #169, #171 and #178, and `App.tsx` by #160, #167, #171 and #184. This caused a merge conflict between #167 and #160. These two files are becoming the place every feature touches, so we should watch their size and split them if needed.
- **Reuse.** #154 reuses the GPS validation from #134. #160 reuses the existing login function. #161 reuses the shared `Difficulty` values, and Master and Polyglot reuse the existing badge rules. #165 reuses `require_teacher`, `require_student` and each class's existing language. #167 uses the `started_at` and `finished_at` columns that `game_sessions` already had, so it needed no migration. #171 reuses the same game fields as start game, so a resumed game opens the same way as a new one. #178 reads the difficulty stored on each game and the attempts already counted for each spot, and keeps the point values in one small helper, `utils/scoring.py`. #180 and #182 use the existing join endpoint and `GET /api/student/profile`, so no backend changes were needed. #182 also moved the "fr" → "French" helper out of `OngoingGames.tsx` into `utils/languageName.ts` so both lists share it. #184 and #186 use the existing teacher class endpoints from earlier weeks, and the shared `utils/languageName.ts` from #182 for language labels.
- **Not trusting the client.** The stopwatch time comes from the backend, so a wrong phone clock can't change it (#167). Room coordinates stay on the server, and a rejected GPS reading doesn't change attempts, points or progress (#154).
- **Schema changes.** `008_student_badges.sql` (#161) and `009_assigned_hunts.sql` (#165). Assigned hunts use `ON DELETE RESTRICT`, which fits our pattern of keeping records for teachers, so a class with hunts can't be deleted. We may need a way to archive hunts later.
- **Configuration.** Clue audio now comes from a folder set by `AUDIO_DIR`, which is bind-mounted in Docker (#169). New or replaced clips no longer need an image rebuild, and this will support teachers uploading audio later. Audio paths live in one module, `utils/audio_storage.py`.
- **Test speed.** The backend suite was slow mostly because every test that creates a user hashes a password with bcrypt. #177 adds a shared `tests/backend/conftest.py` that uses fewer bcrypt rounds in tests only (real passwords keep the normal setting), and CI now caches pip installs between runs.
- **Known debt.** `database_unavailable` is imported from `teacher_access.py` by student code and should move to a shared file. Several tests borrow setup from `test_teacher_access.py`; now that #177 added `conftest.py`, that setup can move there. Resume has no click test yet. Start always makes a new game, so unfinished games can pile up. Assigned hunts aren't linked to games yet.

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
- #178: 60 scoring, answer and game session tests passed against PostgreSQL 17, including a wrong answer earning zero points.
- #182: 75 frontend tests and the build passed. Checked by hand on the Docker stack that a newly joined class appears without a refresh and is still listed after reloading.
- #184: 69 frontend tests and the build passed. Checked by logging in as a teacher and seeing their classes with each join code.
- #186: 77 frontend tests and the build passed. Checked in the browser that a new class is selected straight away with its join code, and that a failed request keeps the typed name and language.

**Manual demo check:** we demoed to the TA on Thursday, October 29, and it went well. The main things to follow up on are tweaking the location check and figuring out elevation.

## Architecture alignment

This sprint adds these data flows:

1. **Signup.** The create account form sends the student's details to the existing signup endpoint, then logs in through the existing login process.
2. **GPS.** The browser captures a fresh location before each photo upload. `POST /api/game/{game_id}/answer` checks it against the current target before running OCR, so GPS, the last missing link from last week, is now connected.
3. **Points by difficulty and attempts.** When an answer is correct, the backend reads the game's stored difficulty and the spot's attempts, then awards points through `utils/scoring.py`: 10, 20 or 30 on the first try, fewer on the second, and a fixed minimum after that.
4. **Badges.** After a correct answer, the backend reads the student's progress and saves any new badges to `student_badges` in the same transaction as the answer. `GET /api/student/badges` returns every badge, earned or locked.
5. **Assigned hunts.** `POST /api/teacher/classes/{class_id}/hunts` checks that the teacher owns the class, takes the class's language, and writes to `assigned_hunts`. `GET /api/student/hunts` reads the hunts for the student's classes.
6. **Game time and resume.** The clue and answer responses now carry the elapsed and final time, worked out from `game_sessions`. `GET /api/game/ongoing` lists the student's unfinished games.
7. **Classes on the dashboards.** Students join a class with `POST /api/student/classes/join` and see their classes through `GET /api/student/profile`. Teachers see their classes through `GET /api/teacher/classes` and create new ones with `POST /api/teacher/classes`.

## Collaboration process and next steps

All PRs targeted `main` and went through teammate review. Reviews caught several issues before merge:

- a confusing "Please fill in every field" message for a username or student number that was too long (#160)
- hardcoded languages, now read from the `languages` table, and a duplicated test helper (#161)
- `ON DELETE CASCADE` on assigned hunts, which would have deleted hunts with their class (#165)
- merging #154 before #155 would have made the game unplayable
- a PR touching 14 files (#167). We discussed it and kept it together, since the changes were small and needed each other
- a teacher dashboard that was more styled than the agreed minimal demo (#173), rebuilt as #184
- a hardcoded language list in the teacher dashboard (#184), so new languages would need a code change. All the language helpers now live together in `utils/` (#184, #186)
- points that ignored attempts (#178), so everyone finishing a game at the same level got the same score and the leaderboard couldn't show who played better. Points now drop with extra attempts
- missing screenshots on frontend PRs (#155, #173, #184, #186), now added so teammates can quickly see what changed
- #182 and #186 carrying another PR's commit, so each waited for the earlier PR to merge first

We are continuing this week on levels with language and difficulty choice. Redeeming points (#156) depends on points, so it follows after. Also planned are the leaderboard, the class roster page (#174), the admin side of the dashboard, and keeping the OCR models in a Docker volume (#148). After the TA demo, we need to tweak the location check and figure out elevation, since it isn't accurate enough yet to tell floors apart. We also need to test GPS and OCR on a real phone on campus, link assigned hunts to games, and add a teacher screen for assigning hunts. Leaving a class needs a backend change first, and we need to make sure teachers can still see students who leave. We still need to ask the client about limits on photo uploads and audio listens.