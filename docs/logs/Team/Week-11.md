# Week 11 Team Log: Team 7

Authors: Ashish, Dan, Gamu, Madiba

November 16–22, 2026

The [Week 10 team log](Week-10.md) covers November 9–15. Dates below use Vancouver time, so several November 23 UTC merges fall on November 22 locally.

## PRs covered

| PR | Author | What | Status |
|---|---|---|---|
| [#238](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/238) | Ashish (nayakashish) | Default profile icon when a student has none equipped | Merged into `main` |
| [#240](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/240) | Gamu (gamurrrrr) | Show the signed-in student's username and student number | Merged into `main` |
| [#243](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/243) | Gamu | Show the building on Basic clues only | Merged into `main` |
| [#244](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/244) | Gamu | Save for later, quit, or keep playing when leaving a game | Merged into `main` |
| [#248](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/248) | Gamu | Count clue audio plays | Merged into `main` |
| [#249](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/249) | Gamu | Student progress details and hardest locations API | Merged into `main` |
| [#250](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/250) | Gamu | Initial assigned-hunt completion backend | GitHub marked merged after an accidental push; reverted in #256 and reopened as #257 |
| [#252](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/252) | Ashish | Upload clue audio for a selected difficulty | Merged into `main` |
| [#254](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/254) | Ashish | Teacher API to add a location and clue | Merged into `main` |
| [#256](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/256) | Ashish | Revert an accidental push before reopening the changes for review | Merged into `main` |
| [#257](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/257) | Ashish, reopening Gamu's #250 work | Link games to assigned hunts and report completion | Merged into `main` |
| [#258](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/258) | Ashish | Select only locations ready for the game's language and difficulty | Merged into `main` |
| [#259](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/259) | Gamu | Update DFDs and system architecture | Merged into `main` |
| [#261](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/261) | Dan (danruk) | French directional clues for Advanced and stories for Expert | Merged into `main` |
| [#263](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/263) | Dan | Skip and replace the current hunt location | Merged into `main` |
| [#265](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/265) | Dan | Record clue audio plays from the game screen | Merged into `main` |
| [#267](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/267) | Madiba (KoesOremus) | GPS-based text hints after five minutes on a clue | Merged into `main` |
| [#269](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/269) | Madiba | Completed-hunt debrief data | Merged into `main` |
| [#271](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/271) | Madiba | Debrief screen and target-language clue text for review | Merged into the #269 feature branch, not `main` at the checked revision |

Statuses and targets were checked against GitHub and fetched Git history through `2132ad6`. PR #271 was merged into `268-add-debrief-data-for-completed-hunts` after #269 had already merged into `main`; its merge commit is not an ancestor of `main` at that revision. Its screen therefore needs a separate path into `main`.

## Goal and work distribution

- **Goal:** prepare the game for the Milestone 1 demo, improve clue and location readiness, and begin exposing student progress and post-hunt support.
- **Ashish** added the default profile icon (#238), difficulty-aware audio upload (#252), teacher location creation (#254), and ready-location selection (#258). He reverted an accidental push (#256) and reopened Gamu's hunt-completion work as #257 for review.
- **Gamu** added student details (#240), Basic-only building display (#243), save/quit choices (#244), clue-play counting (#248), and the progress endpoint (#249). She authored the initial assigned-hunt completion work (#250, reopened as #257) and opened the DFD and architecture update (#259).
- **Dan** added French Advanced directions and Expert stories (#261), location replacement when a student skips (#263), and frontend recording of clue playback (#265).
- **Madiba** added GPS-based hint logic (#267), completed-hunt debrief data (#269), and the dependent debrief and vocabulary screen (#271).

**Did we meet the goal?** The merged backend and game-screen work provides stronger game readiness checks, difficulty-specific content, save/quit and skip flows, and data for student progress and debriefs. The frontend debrief from #271 was merged to a feature branch after its base PR had already merged, so it is not yet part of the checked `main`. A complete demo and regression run on the integrated application remain follow-up work.

## Code-base health

- **Location readiness.** #258 requires a clue in the selected language, a GPS target, and an audio clip for the chosen difficulty before a location can be selected. A hunt still needs five ready locations.
- **Difficulty and content.** #243 hides the building for Advanced and Expert, #252 lets teachers upload audio by difficulty, and #261 gives the five French demo locations distinct Advanced and Expert scripts.
- **Hunt lifecycle.** #244 distinguishes saving an unfinished hunt from quitting it. #263 replaces the current stop with an unused playable location while keeping the hunt's position, time and points.
- **Progress and debrief.** #248 stores clue plays, #265 records them from the game screen, and #249 summarizes finished games and difficult locations. #269 shares completed-location activity with progress and resets clue listens and attempts when a location is skipped, preventing the replacement room from inheriting the skipped clue's counts.
- **Assigned hunts.** #257 links games to assigned hunts and adds completion data for students and teachers. Its PR describes backend work; the separate student-facing start/completion integration still needs verification.
- **Known debt.** Hint audio was not included in #267. Clue recordings are shared across classes using a location. The debrief screen from #271 needs integration into `main`, and location and audio availability still constrain playable languages.

## Testing and validation

These results are recorded in individual logs, PR descriptions, and development runs on different branch states. They are not one final regression run on the current `main`.

| Check | Environment and command | Recorded result | Execution evidence |
|---|---|---|---|
| Default profile icon | Frontend tests and production build | 230 frontend tests passed; type check and build passed | [#238](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/238) |
| Save or quit | Local backend and frontend suites | 787 backend and 232 frontend tests passed | [Gamu's log](../GamuMhere/Week-10-11.md) |
| Clue-listen backend | Local PostgreSQL 17; backend and frontend suites | 862 backend and 237 frontend tests passed | [Gamu's log](../GamuMhere/Week-10-11.md) |
| Progress details | Local PostgreSQL 17; backend and frontend suites | 870 backend and 237 frontend tests passed | [Gamu's log](../GamuMhere/Week-10-11.md) |
| Assigned-hunt completion | Local PostgreSQL 17; tests on #250's code | 864 backend and 237 frontend tests passed | [Gamu's log](../GamuMhere/Week-10-11.md) |
| Skip location | Local PostgreSQL; backend and frontend suites | 856 backend and 237 frontend tests passed; build passed | [#263](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/263) |
| Record audio plays | Local PostgreSQL; backend and frontend suites | 863 backend and 237 frontend tests passed; build passed | [#265](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/265) |
| GPS hints | Focused backend tests; frontend suite and build | 10 hint tests and 238 frontend tests passed; build passed | [#267](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/267) |
| Debrief display | Frontend suite and build; focused backend tests | 243 frontend tests and 11 focused backend tests passed; 74 database-dependent tests skipped in the merge-resolution run | [#271](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/271) and recorded local run |

The #269 review fix added a regression that finishes a hunt after skipping a replayed clue and checks the debrief. It was **not run against PostgreSQL locally**, so the shared aggregation and skip-reset integration still need a database-backed run. In the full backend run on #271, 520 tests passed, 8 failed, 28 errored and 373 were skipped with PostgreSQL unavailable.

**CI limitation:** GitHub Actions reported that jobs could not start because the account was locked due to a billing issue. The recorded local checks do not establish a passing CI run or a single final regression result.

## Architecture and DFD alignment

The updated diagrams are linked from the [system architecture](../../design/system_architecture.png), [Level 0 DFD](../../design/DFDs/dfd-level0.png), [Level 1 DFD](../../design/DFDs/main-dfd-level1.png), and detailed [game](../../design/DFDs/game-dfd.png), [class](../../design/DFDs/class-dfd.png), [authentication](../../design/DFDs/auth-dfd.png), and [user management](../../design/DFDs/user-dfd.png) diagrams. #259 merged documentation updates during this period.

The week's changes add or extend these flows:

1. **Teacher content:** teachers select a difficulty when uploading audio and can add a location and clue through protected endpoints. Gameplay only selects locations with the required clue, GPS target and difficulty-specific audio.
2. **Hunt activity:** students can save, quit or replace a location. The frontend records clue playback through the backend so completed-game progress can use the stored counts.
3. **Assigned hunts:** starting a linked hunt records its hunt ID; the backend can report completion and outcomes for enrolled students.
4. **Hints:** after five minutes on a clue, the game sends a fresh location reading to the backend, which returns a text hint based on distance from the target.
5. **Debrief:** the protected backend aggregates completed-hunt activity and identifies difficult locations. #271 adds the display and matching language's clue text on its feature branch; that screen still needs to reach `main`.

## Collaboration process and next steps

The team reviewed related backend and frontend changes in sequence. The accidental direct push involving #250 and readiness work was reverted in #256 and the work reopened through #257 and #258. Review of the debrief also identified that a skipped clue's listens could be attributed to its replacement; #269 resets both listens and attempts and adds a finished-hunt regression. The progress and debrief endpoints now share their activity aggregation while retaining their different ranking rules.

Next steps are to bring #271's changes into `main`, run the PostgreSQL regression and full integrated suite, restore GitHub Actions, and verify student, teacher and admin demo paths on real devices. The team should also follow up on target-language hint audio and confirm that each offered language has enough playable locations and recordings. No application tests were rerun while writing this documentation.
