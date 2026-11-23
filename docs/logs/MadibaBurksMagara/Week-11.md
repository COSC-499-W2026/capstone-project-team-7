### Week 11 — Madiba Burks Magara

November 16–22, 2026

This week I worked on GPS-based hints and a post-hunt debrief. I opened [PR #267 — Add GPS-based hints after five minutes on a clue](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/267), [PR #269 — Add debrief data for completed hunts](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/269), and [PR #271 — Display post-hunt debrief and vocabulary suggestions](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/271).

All three PRs were open when I wrote this log; #269 was a draft. #271 targets the #269 branch so its display changes can be reviewed separately from the backend data. None of the three is reported here as merged. The test results below are recorded runs from the respective branches, not a new regression run for this log.

---

### For PR #267 — Add GPS-based hints after five minutes on a clue

- [x] For [issue #266](https://github.com/COSC-499-W2026/capstone-project-team-7/issues/266), I added a five-minute timer for the current clue. The timer survives page reloads and continues while the student is away from the game.
- [x] I added a migration for the clue start time and reset the timer when the student completes or skips a clue. Existing games start the timer when the migration is applied.
- [x] I added a protected hint endpoint that checks the current clue and uses a fresh GPS reading. At 10 metres or less from the target it returns “You are getting close”; beyond 10 metres it returns “You are too far.”
- [x] I reused the existing proximity calculation and GPS validation. Stale or insufficiently accurate readings are rejected; the game screen offers a retry if the hint cannot be loaded.
- [x] I added the hint display to the game screen and documented the timing, GPS requirements and migration in the README. The hint is text only; target-language audio remains follow-up work.
- [x] In the DFD, the game screen requests a device location and sends it to the protected backend hint endpoint. The backend compares the reading with the current target and returns a hint without sending the target coordinates to the student.

For Tests:

- [x] The focused hint endpoint run passed **10 tests**, covering the five-minute gate, 10-metre boundary, stale or inaccurate readings, invalid input, changed clues, missing target coordinates and login.
- [x] The frontend suite passed **238 tests**, and the production build passed.
- [ ] Database-backed timer-reset tests remain unverified because local PostgreSQL was unavailable. The full backend suite did not pass in that environment.

---

### For PR #269 — Add debrief data for completed hunts

- [x] For [issue #268](https://github.com/COSC-499-W2026/capstone-project-team-7/issues/268), I added the student-only `GET /api/student/debrief` endpoint.
- [x] The endpoint counts the student's completed, non-quit hunts and returns up to three difficult locations. It excludes unfinished hunts and other students' games.
- [x] I used repeated clue listens or photo attempts as signs of difficulty. Results are grouped by location, language and difficulty, then ranked by extra attempts and clue listens. Each result includes the underlying counts.
- [x] When the student has no completed hunts, the endpoint returns a zero count and an empty list. The student-facing prompt and vocabulary display are handled in the dependent PR.
- [x] I documented the response, access rules and error handling in the README. No schema migration was added for this endpoint.
- [x] In the DFD, a signed-in student requests a debrief through the backend; PostgreSQL supplies completed sessions, clue-listen counts and photo-attempt counts, and the API returns an aggregate for display.

For Tests:

- [x] **3 debrief unit tests passed**, including the protected endpoint's safe database-failure response and request behavior.
- [x] The frontend suite passed **238 tests** on this branch.
- [ ] The PostgreSQL integration tests for completed-hunt aggregation, empty results and access control were skipped because the local database was unavailable.
- [ ] GitHub Actions jobs did not start: the workflow annotation reported an account billing lock. This does not establish a passing CI run.

---

### For PR #271 — Display post-hunt debrief and vocabulary suggestions

- [x] For [issue #270](https://github.com/COSC-499-W2026/capstone-project-team-7/issues/270), I added a debrief page accessible from the student dashboard and the finished-hunt screen.
- [x] The page displays the completed-hunt count and difficult locations with their language, difficulty, clue listens and photo attempts. It explains when no particular difficulties were recorded.
- [x] I extended the backend response to include the difficult clue's number and description text in the hunt language. The page presents this text as vocabulary to review and handles missing clue text without dropping the location.
- [x] Students with no completed hunts see a prompt to complete one first. Request failures offer a retry, and expired sessions return the student to login.
- [x] I added frontend and backend coverage and updated the README. The PR is based on #269 because it uses that PR's endpoint.
- [x] In the DFD, the dashboard or finished-hunt screen requests the student's debrief from the backend. The backend joins the recorded difficulty data to the matching language's clue text, and the frontend presents the results for review.

For Tests:

- [x] The frontend suite passed **243 tests**, including debrief rendering, the no-hunts state, missing vocabulary, session expiry and request errors. The production build passed.
- [x] **3 debrief backend unit tests passed**; the PostgreSQL integration tests were skipped locally.
- [ ] The full backend run reported **520 passed, 8 failed, 28 errors and 373 skipped** with PostgreSQL unavailable. The database-backed vocabulary and aggregation behavior still needs verification.

---

## How this fits the overall system

The hint work connects clue timing and GPS proximity to the game screen, giving students a text prompt when they spend five minutes on one clue. The debrief work uses completed-hunt activity to identify clues that may need review and presents their target-language text after play. The debrief data and interface are split into dependent PRs, so the backend can be reviewed independently.

Next steps are to run the PostgreSQL integration tests, resolve the GitHub Actions billing lock, and review and merge the dependent PRs in order. Hint audio remains separate work. No application tests were rerun while writing this log.
