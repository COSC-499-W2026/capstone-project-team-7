# Week 7 Team Log: Team 7

Authors: Ashish, Dan, Gamu, Madiba

October 19–25, 2026

## PRs covered

| PR | Author | What | Status |
|---|---|---|---|
| [#108](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/108) | Ashish (nayakashish) | Random picker for 5 distinct hunt locations | Merged |
| [#114](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/114) | Ashish (nayakashish) | Teachers view the roster of a class they own | Merged |
| [#117](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/117) | Gamu (gamurrrrr) | Demo: basic login page connected to the backend | Merged |
| [#120](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/120) | Gamu (gamurrrrr) | Demo: start game endpoint and game session tables | Merged |
| [#121](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/121) | Gamu (gamurrrrr) | Demo: basic student dashboard | Merged |
| [#123](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/123) | Gamu (gamurrrrr) | Demo: 5 demo locations with French clues and audio clips | Merged |
| [#125](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/125) | Gamu (gamurrrrr) | Demo: current clue and clue audio endpoints | Merged |
| [#127](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/127) | Gamu (gamurrrrr) | Demo: game screen with clue audio player | Merged |
| [#129](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/129) | Gamu (gamurrrrr) | Demo: submit answer endpoint | Merged |
| [#132](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/132) | Gamu (gamurrrrr) | Demo: live camera photo page | Merged |
| [#133](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/133) | Ashish (nayakashish) | Demo: send the photo answer, finish screen | Merged |
| [#134](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/134) | Dan (danruk) | GPS proximity validation and location coordinates | Merged |
| [#136](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/136) | Madiba (KoesOremus) | OCR of building and room numbers from photos | Merged |
| [#137](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/137) | Dan (danruk) | Demo target coordinates with a 50-metre arrival radius | Merged |
| [#140](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/140) | Dan (danruk) | Students read their own account details | Merged |
| [#143](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/143) | Madiba (KoesOremus) | OCR photo verification in the answer endpoint, 10 points per spot | Merged |
| [#145](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/145) | Madiba (KoesOremus) | Frontend: send photos to verification, show points | Merged |
| [#147](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/147) | Ashish (nayakashish) | Send the student back to the login page when their session ends mid-game | Merged |
| [#139](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/139) | Ashish, Gamu | Docs: updated game DFD, frontend mockups (3 styles), meeting minutes | Merged |

## Goal and work distribution

- **Goal:** build a minimal working demo to show the professor and TA at our weekly session. A student should be able to log in, start a game, hear a clue, take a photo of the room number, and move through all 5 spots to a finish screen. The focus was on getting the OCR and GPS features in, then the minimal frontend.
- To keep the demo small, every game is French on Basic difficulty. The screens are plain on purpose as frontend will be built up in milestone 2.
- **Ashish** built the location picker used by start game (#108), the class roster endpoint (#114), the frontend step that sends the photo and shows the finish screen (#133), and the return to the login page when a session ends mid-game (#147). Also updated and reviewed dfds to better explain and build the system.
- **Gamu** built most of the student flow, endpoints and screens: login (#117), start game (#120), dashboard (#121), demo locations and French audio (#123), clue and audio endpoints (#125), game screen (#127), submit answer (#129), and the camera page (#132). ALso created mockup designs of the frontend for client demo and team discussion. 
- **Dan** built GPS proximity validation with location coordinates (#134), set the demo targets' coordinates and arrival radius (#137), and added the student's own account endpoint (#140).
- **Madiba** built OCR that reads building and room identifiers from a photo (#136), then connected it to the answer endpoint with points (#143) and the frontend (#145).

**Did we meet the goal?** Yes. On `main` today a student can log in, open the dashboard, start a game with 5 random spots, hear each spot's French audio clue, and take a photo with the live camera. Then the system checks it and proceeds based on the answer. OCR reads the building and room number from the photo, a correct room earns 10 points and moves to the next spot, and after the 5th spot the finish screen shows the total. GPS validation is built in the backend but is not checked on each answer yet.


## Code-base health

- **Dependent PR chains.** The demo flow split into many small PRs that build on each other (login → dashboard → start game → game screen → photo page → answer). Reviews often found bugs only visible with the next PR, e.g. every spot reused the same audio URL (fixed in #125 before merge). Next sprint we'll count how many PRs a task needs before assigning it, so the chain doesn't sit with one person.
- **Overlapping PRs.** #133 and #145 both added `api/answer.ts` and changed `App.tsx` and the photo page, so they conflicted. In review we agreed #145 would be rebuilt on top of #133 instead of replacing it, so there is one answer flow (with #145 adding points and keeping the photo after a failed send). Next sprint we'll say on the issue who owns each file before starting.
- **Reuse.** Start game reuses the location picker (#108) and the shared auth dependencies. Demo coordinates (#137) reuse the demo location list from #123. #143 reuses `MAX_PHOTO_BYTES` from the OCR module. #147 reuses the existing logout path to show the login page. The frontend calls the backend only through one small file per endpoint in `src/frontend/src/api/`.
- **Not leaking answers.** Start game and the clue endpoint never return room numbers as text, and the audio URL uses the spot position, not the room. Students can't read the answer from the network tab.
- **Schema changes.** `005_game_sessions.sql` (#120), `006_location_coordinates.sql` (#134) and `007_photo_verification_points.sql` (#143). #134 was renamed from `005` in review so there are no more duplicate numbers. Game sessions keep `student_id` with no `ON DELETE SET NULL`, so teachers keep past games. Account deletion will deactivate instead of deleting.
- **Dependencies.** OCR (#136) adds PaddleOCR and PaddlePaddle in an optional `requirements-ocr.txt`. CI installs only `requirements.txt`, and OCR tests use fake predictions. #143 installs OCR in the Docker image, which makes it much bigger. The models download on first use, so they should go in a Docker volume so rebuilds don't download them again (#148). This is planned for a future pr. 

## Testing and validation

| Check | Environment and command | Result | Execution evidence |
|---|---|---|---|
| Full backend | Ubuntu, Python 3.13, PostgreSQL 17; `python -m pytest tests/backend` | Passed: 548 tests on `main` at `07951e7` | [CI backend job](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/40253077768/job/121348980692) |
| Frontend build and tests | Ubuntu, Node 22; `npm ci`, `npm run build`, `npm test` | Passed: 40 tests, 7 files (also run locally) | [CI frontend job](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/40253077768/job/121348980400) |

Also checked in review:

- #143: its game and answer test files gave 40 passed against PostgreSQL 17, including a real concurrent double-submit test (two correct photos at once award points only once).
- #145: 40 frontend tests and the build pass. Checked in a headless browser with a fake camera.
- #147: 31 frontend tests and the build pass. Checked by hand by deleting the session cookie mid-game.

**Manual demo check:** run locally on a laptop (`localhost`). Login → Start game → audio → camera photo → Submit → next spot, and each spot's audio played a different number. We haven't tried it on a phone on campus yet as none of us were on campus this weekend for testing, however using mock data and devtools we are able to confirm basic functionality. We will also need HTTPS for the camera and the session cookie, and real door sign photos for the OCR.

## Architecture and DFD alignment

This sprint adds the first game data flows:

1. The student logs in through the existing session-cookie auth.
2. `POST /api/game/start` picks 5 locations and stores them in `game_sessions` and `game_session_locations`.
3. The game screen asks for the current clue and streams its French audio.
4. The photo goes to `POST /api/game/{game_id}/answer`. OCR reads the room from the photo and compares it with the current target. A match awards 10 points and moves the game to the next spot; every photo counts as an attempt.

The OCR and GPS processes from the architecture diagram now exist in the backend. OCR reads the building and room number from the photo. GPS validation checks the reading's age and accuracy, and its distance from the target's stored coordinates and radius. #143 connects OCR to the answer step and stores points on the game. GPS is the remaining link: the answer request needs a way to carry the reading with the photo. We also tested with elevation, however were finding that the altitude report was highly inconsistent and was not feasible. Due to the findings, we discussed as a team and deferred that for a following week, after we can read up or test more on how to differentiate between building floors. 

We also updated the Game Loop DFD to be more detailed and clearer for development this week:
[game-dfd.png](../../design/DFDs/game-dfd.png)

## Collaboration process and next steps

All PRs targeted `main` and went through teammate review. Reviews caught several bugs before merge:

- the same audio URL for every spot
- `ON DELETE SET NULL` on game sessions
- a duplicate `005` migration
- the photo being read before the login check
- two PRs building the same answer flow

The demo PRs were kept small to stay within size limits, which caused the review chain noted above. Though Gamu had many PRs this week for building up the demo, the team remained in contact through our group chat to ensure she was not overworked. She made the changes one after another and explained to the team the process in changes. We have discussed this as a team in multiple meetings and for continuing weeks, if this situation arises again, once brought up to the team we will split up tasks between members more equally. This will not only prevent one member from potentially becoming overrun by tasks, but will also distribute the workload more evenly across the team, and ensure that everyone has a clear understanding of the changes being made throughout the development process.

Next steps are to present the demo to the professor and TA and record their feedback, then test OCR on real phone photos at the demo rooms. GPS validation is built but not yet connected, so the answer request needs to carry the student's location with the photo, and the 50-metre radius needs testing on site. The OCR models should move to a Docker volume so they download only once (#148). After that, the team will add language and difficulty choice, more locations, and points on the class roster.
