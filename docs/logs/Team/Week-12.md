# Week 12 Team Log: Team 7

Authors: Ashish, Dan, Gamu, Madiba

November 23–29, 2026


## PRs covered

| PR | Author | What | Status |
|---|---|---|---|
| [#275](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/275) | Gamu (gamurrrrr) | Polyglot Legend needs every difficulty in every language; badges grouped by language | Open, approved |
| [#276](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/276) | Gamu | Demo: teacher account signup | Open, approved |
| [#279](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/279) | Gamu | Teacher class report: per-student summary (part 1 of #277) | Open, approved |
| [#280](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/280) | Gamu | Teacher class report: hardest levels and CSV export (part 2 of #277) | Open, changes requested and fixed, waiting for re-review |
| [#282](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/282) | Gamu | Demo: teacher class report screen | Open, targets the #280 branch |
| [#284](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/284) | Gamu | Demo: teacher class leaderboard (split out of #276) | Open |
| [#286](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/286) | Ashish (nayakashish) | Tables and file storage for teachers' own location clips | Open, approved |
| [#288](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/288) | Ashish | Teacher API to add, list, play and retire their own clips | Open, approved |
| [#290](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/290) | Ashish | "My clips" section on the teacher dashboard | Open, approved |


## Goal and work distribution

- **Goal:** after the Milestone 1 client demo on November 19, continue the teacher-side items from the November 17 meeting: "Class stats" so teachers can see how their students are doing, and a better answer to teacher audio, where one upload replaced the clip for every class. We also built plain demo screens for the Milestone 1 video.
- **Gamu** built the teacher class report: a per-student summary (#279), then the hardest levels and a CSV download (#280), with a demo screen to view and download it (#282). She also made Polyglot Legend harder (#275), added teacher signup to the create-account page (#276), and a class leaderboard on the teacher dashboard (#284).
- **Ashish** started teachers' own location clips, so a teacher can add extra clips without replacing the shared default: the tables and file storage (#286), the API (#288) and a "My clips" dashboard section (#290).


**Did we meet the goal?** Partly. Teachers now have a class report with a CSV export, a class leaderboard and their own clips, and each piece has a PR with tests. But nothing has merged into `main` yet, so none of it is in the hosted demo. The debrief screen from #271 is also still not in `main`, as noted last week.

## Code-base health

- **Reuse.** The class report counts the same games as the class leaderboard through one shared rule, `CLASS_GAMES` (#279, #280), and the teacher leaderboard reuses the student leaderboard's `class_rankings()` (#284). #286 moved the safe temp-file write into a shared `replace_file()`, and #290 moved the difficulty list into `utils/difficulties.ts`.
- **Data the report needed.** Skipping a clue used to reset its plays and photo attempts to 0, which meant the report lost them. Migrations `019` and `020` save them in `skipped_location_listens` and `skipped_location_attempts` first. Skips from before these migrations count as 0.
- **Fair "hardest levels".** Review on #280 found that total plays and attempts mostly showed how often a room was picked, because every clue is played once and every found room takes one right photo. It now counts only extra plays and wrong photos, and each list shows the top 5.
- **Schema changes.** `019` and `020` (#279, #280) and `021_location_clips.sql` (#286). #286 used `021` because `019` and `020` were already taken by open branches, and the migrations touch different columns, so they can merge in any order.
- **Privacy.** A teacher's own clip is private: another teacher's clip, a retired clip and an unknown id all return 404 "Clip not found" (#288). The report returns no emails, passwords or student numbers (#279).
- **Known debt.** `game_session_locations.clip_id` only checks the clip id, so a round could save another room's clip; `hunt_clips` already blocks this with a composite key (review on #286). Retired clips stay in `hunt_clips`, so the game start code will need to skip them (review on #288). An approved teacher email can still sign up as a student (#276). The demo screens are plain on purpose and will be redesigned in Milestone 2.

## Testing and validation
.

| Check | Environment and command | Recorded result | Execution evidence |
|---|---|---|---|
| Harder Polyglot Legend | Local PostgreSQL 17; backend and frontend suites | 948 backend and 238 frontend tests passed | [#275](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/275) |
| Teacher signup | Local PostgreSQL; backend and frontend suites | 943 backend and 244 frontend tests passed; build passed | [#276](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/276) |
| Class report, part 1 | Local PostgreSQL; backend suite | 950 backend tests passed | [#279](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/279) |
| Hardest levels and CSV | Local PostgreSQL; backend suite | 960 backend tests passed, after the review fix | [#280](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/280) |
| Report screen | Local PostgreSQL; backend and frontend suites | 958 backend and 245 frontend tests passed; build passed | [#282](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/282) |
| Teacher leaderboard | Local PostgreSQL; backend and frontend suites | 951 backend and 245 frontend tests passed; build passed | [#284](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/284) |
| Clip tables and storage | `TEST_DATABASE_URL` set; backend and frontend suites | 966 backend tests passed with none skipped; 238 frontend | [#286](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/286) |
| Own clips API | `TEST_DATABASE_URL` set; backend and frontend suites | 994 backend tests passed with none skipped; 238 frontend | [#288](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/288) |
| My clips section | Frontend suite and build | 254 frontend tests passed; build passed | [#290](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/290) |

Also checked:

- #280: a new test for the reviewer's example (a room found first try in 5 games next to a room that took 4 photos once) failed on the old totals and passes after the fix.
- #282: checked by hand without Docker, using a local PostgreSQL database with demo students, games and a quit game. The report, hardest levels and CSV download all matched the backend.

**CI limitation:** GitHub Actions still can't start jobs because of the billing lock, so every run this week failed within seconds without running a test. The local results above don't replace a passing CI run.

## Architecture and DFD alignment

The diagrams are linked from the [system architecture](../../design/system_architecture.png), [Level 0 DFD](../../design/DFDs/dfd-level0.png), [Level 1 DFD](../../design/DFDs/main-dfd-level1.png), and detailed [game](../../design/DFDs/game-dfd.png), [class](../../design/DFDs/class-dfd.png), [authentication](../../design/DFDs/auth-dfd.png), and [user management](../../design/DFDs/user-dfd.png) diagrams. They were not updated this week; the new teacher flows below should be added once the PRs merge.

This week's PRs add these flows:

1. **Class report.** `GET /api/teacher/classes/{class_id}/report` checks the teacher owns the class, then reads the class's finished games in its language for enrolled students and returns a row per student plus the hardest levels. `.../report.csv` returns the same data as a CSV file named after the class and today's date in Vancouver.
2. **Saving skipped clue counts.** When a student skips, the game saves the skipped clue's plays and photo attempts before resetting them, so the report keeps them.
3. **Teacher leaderboard.** `GET /api/teacher/classes/{class_id}/leaderboard` returns the same ranking students see, for a class the teacher owns.
4. **Teacher signup.** The create-account page sends teachers to the existing `POST /api/auth/teacher/signup`, which only accepts emails an admin approved.
5. **Teachers' own clips.** A teacher uploads an MP3 for a room and difficulty, which is saved in `location_clips` and at `<language>/clips/<clip id>.mp3`. They can list, play and retire their own clips from the "My clips" section. Games still play the default clips; choosing a clip per room in a hunt is the next PR.

## Collaboration process and next steps

All PRs targeted `main` (except #282, stacked on #280) and went through teammate review. Ashish reviewed Gamu's PRs and Gamu reviewed Ashish's. Reviews caught:

- hardest levels that ranked how often a room was picked, not how hard it was (#280), fixed by counting only extra plays and wrong photos
- `clip_id` not checking that a clip belongs to the round's room (#286)
- retired clips staying in `hunt_clips`, which the hunt clip PR will need to handle (#288)

#276 started as two features in 10 files, so the class leaderboard was split into its own PR (#284) to keep each review small. Ashish noted on #290 that the clip screens are plain for now and will be redone with the Milestone 2 frontend.

Next steps: merge #279, #280 and #282 in order once #280 is re-reviewed, then merge the rest; bring the #271 debrief screen into `main`; add hunt clip choices and fix the two clip issues from review; update the DFDs with the new teacher flows; restore GitHub Actions and do one full regression run on `main`.
