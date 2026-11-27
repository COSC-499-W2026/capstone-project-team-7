# Week 12 Team Log: Team 7

Authors: Ashish, Dan, Gamu, Madiba

November 23–29, 2026


## PRs covered

Statuses were checked against GitHub on November 27.

| PR | Author | What | Status |
|---|---|---|---|
| [#275](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/275) | Gamu (gamurrrrr) | Polyglot Legend needs every difficulty in every language; badges grouped by language | Merged into `main` |
| [#276](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/276) | Gamu | Demo: teacher account signup | Merged into `main` |
| [#279](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/279) | Gamu | Teacher class report: per-student summary (part 1 of #277) | Merged into `main` |
| [#280](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/280) | Gamu | Teacher class report: hardest levels and CSV export (part 2 of #277) | Merged into `main` after a requested change |
| [#282](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/282) | Gamu | Demo: teacher class report screen | Merged into `main` |
| [#284](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/284) | Gamu | Demo: teacher class leaderboard (split out of #276) | Merged into `main` |
| [#286](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/286) | Ashish (nayakashish) | Tables and file storage for teachers' own location clips | Open, approved |
| [#288](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/288) | Ashish | Teacher API to add, list, play and retire their own clips | Open, changes requested and fixed, approved |
| [#290](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/290) | Ashish | "My clips" section on the teacher dashboard | Open, approved |
| [#292](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/292) | Ashish | Teachers choose one of their own clips per room when assigning a hunt | Open, approved |
| [#294](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/294) | Ashish | Hunt games play the teacher's chosen clips, falling back to the default | Open, changes requested and fixed, waiting for Dan's re-review |
| [#296](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/296) | Ashish | Clip choices in the assign hunt form | Open, approved by Gamu, waiting for a second review |


## Goal and work distribution

- **Goal:** after the Milestone 1 client demo on November 19, continue the teacher-side items from the November 17 meeting: "Class stats" so teachers can see how their students are doing, and a better answer to teacher audio, where one upload replaced the clip for every class. We also built plain demo screens for the Milestone 1 video.
- **Gamu** built the teacher class report: a per-student summary (#279), then the hardest levels and a CSV download (#280), with a demo screen to view and download it (#282). She also made Polyglot Legend harder (#275), added teacher signup to the create-account page (#276), and a class leaderboard on the teacher dashboard (#284).
- **Ashish** started teachers' own location clips, so a teacher can add extra clips without replacing the shared default: the tables and file storage (#286), the API (#288) and a "My clips" dashboard section (#290). He then let teachers choose a clip per room when assigning a hunt (#292), made hunt games play those clips (#294), and added the choices to the assign hunt form (#296).
- **Dan** reviewed most of the week's PRs and requested two changes that were fixed before approval: a clip row that was saved before its MP3 (#288), and private clip labels shown to a new teacher after a class is reassigned (#294).


**Did we meet the goal?** Mostly. The class report with hardest levels and a CSV export, the teacher leaderboard and teacher signup are all merged into `main`. Teachers' own clips are complete across six PRs, from storage to choosing clips in a hunt, but they are still in review. The debrief screen from #271 is still not in `main`, as noted last week.

## Code-base health

- **Reuse.** The class report counts the same games as the class leaderboard through one shared rule, `CLASS_GAMES` (#279, #280), and the teacher leaderboard reuses the student leaderboard's `class_rankings()` (#284). #286 moved the safe temp-file write into a shared `replace_file()`, and #290 moved the difficulty list into `utils/difficulties.ts`, which #296 then reused. #292 reuses `own_clips` from the clip API to check each hunt choice.
- **Data the report needed.** Skipping a clue used to reset its plays and photo attempts to 0, which meant the report lost them. Migrations `019` and `020` save them in `skipped_location_listens` and `skipped_location_attempts` first. Skips from before these migrations count as 0.
- **Fair "hardest levels".** Review on #280 found that total plays and attempts mostly showed how often a room was picked, because every clue is played once and every found room takes one right photo. It now counts only extra plays and wrong photos, and each list shows the top 5.
- **Schema changes.** `019` and `020` (#279, #280) and `021_location_clips.sql` (#286). #286 used `021` because `019` and `020` were already taken by open branches, and the migrations touch different columns, so they can merge in any order.
- **Privacy.** A teacher's own clip is private: another teacher's clip, a retired clip and an unknown id all return 404 "Clip not found" (#288), and an invalid hunt choice gives the same 422 whether the clip is someone else's, retired or missing (#292). After review, the hunt list only shows the requesting teacher's clips (#294). The report returns no emails, passwords or student numbers (#279).
- **Safe fallbacks.** A hunt saves its clip choice on each round when the game starts, so later changes don't affect a game in progress. A retired clip or a missing file plays the default clip instead (#294).
- **Known debt.** `game_session_locations.clip_id` only checks the clip id; `hunt_clips` already blocks another room's clip with a composite key (review on #286). A chosen clip only plays if its room is one of the hunt's 5 random rooms (#292). The teacher leaderboard doesn't refresh when the roster changes (#284). An approved teacher email can still sign up as a student (#276). The demo screens are plain on purpose and will be redesigned in Milestone 2.

## Testing and validation

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
| Hunt clip choices | `TEST_DATABASE_URL` set; backend and frontend suites | 1004 backend passed and 8 skipped (they need `DATABASE_URL` and don't touch clips); 238 frontend | [#292](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/292) |
| Hunt clip playback | `TEST_DATABASE_URL` set; backend and frontend suites | 1022 backend tests passed with none skipped; 238 frontend | [#294](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/294) |
| Assign hunt clip choices | Frontend suite | 261 frontend tests passed | [#296](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/296) |
| `main` after the merges | Local PostgreSQL; full suites and build on `main` at `89597cf` (after #284, before #282) | 973 backend and 251 frontend tests passed; build passed | Local run |

Also checked:

- #280: a new test for the reviewer's example (a room found first try in 5 games next to a room that took 4 photos once) failed on the old totals and passes after the fix.
- #282: checked by hand without Docker, using a local PostgreSQL database with demo students, games and a quit game. The report, hardest levels and CSV download all matched the backend.

**CI limitation:** GitHub Actions still can't start jobs because of the billing lock, so every run this week failed within seconds without running a test. The local results above don't replace a passing CI run.

## Architecture and DFD alignment

The diagrams are linked from the [system architecture](../../design/system_architecture.png), [Level 0 DFD](../../design/DFDs/dfd-level0.png), [Level 1 DFD](../../design/DFDs/main-dfd-level1.png), and detailed [game](../../design/DFDs/game-dfd.png), [class](../../design/DFDs/class-dfd.png), [authentication](../../design/DFDs/auth-dfd.png), and [user management](../../design/DFDs/user-dfd.png) diagrams. They were last updated in #259 (November 21). This week's work adds no new entities or data stores, and each flow fits an existing process:

1. **Class report (5.0 Class Management).** `GET /api/teacher/classes/{class_id}/report` and `.../report.csv` read the class's finished games from D1, like 5.10 View Hunt Completion. Skipping a clue in 2.0 Play Game now also saves its plays and photo attempts, so the report doesn't lose them.
2. **Teacher leaderboard (5.8 View Class Leaderboard).** Teachers now get the same rankings students see, through a teacher route that checks class ownership.
3. **Teacher signup (1.0 Authenticate User).** The create-account page sends teachers to the existing teacher signup, which only accepts emails an admin approved.
4. **Teachers' own clips (6.0 Manage Level Content).** Teachers add, list, play and retire their own clips. Clip details go in D1 (`location_clips`) and the MP3s in D2 Clue Audio Files.
5. **Hunt clips (5.4 Assign Hunts and 2.0 Play Game).** A teacher can choose one of their own clips per room when assigning a hunt, saved in `hunt_clips`. A hunt game plays the chosen clip from D2, or the default clip if it was retired or its file is missing.


## Collaboration process and next steps

All PRs went through teammate review: Dan reviewed most PRs, Ashish reviewed Gamu's, and Gamu reviewed Ashish's. Reviews caught:

- hardest levels that ranked how often a room was picked, not how hard it was (#280), fixed by counting only extra plays and wrong photos
- `clip_id` not checking that a clip belongs to the round's room (#286)
- retired clips staying in `hunt_clips` (#288), which #292 and #294 now leave out
- a clip row saved before its MP3, which could list a clip with no audio (#288), fixed before approval
- a new teacher seeing the previous teacher's private clip labels after a class is reassigned (#294), fixed with a clip ownership check and a reassignment test
- the teacher leaderboard not refreshing when the roster changes (#284), left for the Milestone 2 dashboard

#276 started as two features in 10 files, so the class leaderboard was split into its own PR (#284) to keep each review small. Ashish noted on #290 that the clip screens are plain for now and will be redone with the Milestone 2 frontend.

#284 conflicted with `main` after #279 merged, because both added a router line in the same spot in `main.py`; keeping both lines fixed it.

Next steps: merge Ashish's clip PRs in order (#286, #288, #290, #292, #294, #296), pulling `main` into each; bring the #271 debrief screen into `main`; add the small DFD label updates for the report and own clips; restore GitHub Actions and do one full regression run on `main`.
