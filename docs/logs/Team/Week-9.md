# Week 9 Team Log: Team 7

Authors: Ashish, Dan, Gamu, Madiba

November 2–8, 2026

## PRs covered

| PR | Author | What | Status |
|---|---|---|---|
| [#193](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/193) | Gamu (gamurrrrr), with Ashish’s diagram updates | Updated DFDs, system architecture, README and November 3 meeting minutes | Merged |
| [#194](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/194) | Gamu (gamurrrrr) | Student page showing earned and locked badges | Merged |
| [#196](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/196) | Gamu (gamurrrrr) | Teacher dashboard form for assigning hunts to a class | Merged |
| [#198](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/198) | Ashish (nayakashish) | Backend methods for owned and equipped profile icons | Merged |
| [#200](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/200) | Ashish (nayakashish) | Profile icon artwork, shared renderer and demo seed | Merged |
| [#202](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/202) | Ashish (nayakashish) | Teacher API to view locations and upload clue audio | Merged |
| [#204](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/204) | Gamu (gamurrrrr) | List and remove assigned hunts, with an option to show past-due hunts | Merged |
| [#205](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/205) | Gamu (gamurrrrr) | Store endpoints to redeem game points for profile icons | Merged |
| [#206](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/206) | Gamu (gamurrrrr) | Student icon store page and updated badge artwork | Merged |
| [#209](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/209) | Dan (danruk) | Generate clue text and audio for Basic, Advanced and Expert | Merged |
| [#210](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/210) | Dan (danruk) | Serve clue audio using the game’s saved difficulty | Merged |
| [#212](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/212) | Dan (danruk) | Backend language and difficulty selection when starting a game | Merged |
| [#215](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/215) | Dan (danruk) | Frontend language and difficulty selection form | Merged |
| [#217](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/217) | Madiba (KoesOremus) | Class leaderboard API with points, ranks and equipped icons | Merged |
| [#219](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/219) | Madiba (KoesOremus) | Student class leaderboard screen | Merged |
| [#221](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/221) | Madiba (KoesOremus) | Admin dashboard for teacher approvals and class reassignment | Merged |

All 16 PRs above merged into `main` during November 2–8, as confirmed against the fetched Git history through `2223aa0`. This includes the latest merges: #204, #202 and #193.

## Goal and work distribution

- **Goal:** continue last week's demo work by exposing language and difficulty choices, letting students use their rewards, adding the class leaderboard and admin dashboard, and extending teacher hunt management.
- **Ashish** added profile icon ownership and equipping (#198), icon artwork and a reusable renderer (#200), and teacher endpoints for listing locations and uploading MP3 clues (#202). He also updated the architecture, DFDs and README included in #193.
- **Gamu** added the badges page (#194), the teacher hunt-assignment form (#196), the assigned-hunt list and removal flow (#204), points redemption (#205), and the student icon store (#206). She also contributed the November 3 meeting minutes and opened the documentation merge (#193).
- **Dan** added difficulty-specific clue generation (#209), connected playback to the game's saved difficulty (#210), and implemented language and difficulty selection in the backend (#212) and frontend (#215).
- **Madiba** added the class leaderboard API (#217), its student screen with equipped profile icons (#219), and an admin dashboard for approving teacher emails and reassigning classes (#221).

**Did we meet the goal?** The planned feature additions above are merged. Students can choose a language and difficulty, view badges, spend earned points on icons, equip them and view their class leaderboard. Teachers can assign, list and remove hunts through the dashboard. The admin dashboard connects existing account-management operations. Teacher location listing and audio upload are available through the API, with a frontend form still to follow. Content readiness and a final integrated demo check remain necessary: offering six languages does not mean every language already has enough locations and audio.

## Code-base health

- **Reuse.** The store uses Ashish's existing icon listing, equip endpoint and `ProfileIcon` component; the leaderboard also uses that renderer. The badges page reads the existing badges API. Teacher assignment uses the existing hunt endpoint, while listing and removal reuse teacher class-ownership checks.
- **Checks on the backend.** Game creation validates the language and difficulty before database access. Playback reads the stored difficulty, so a query parameter cannot request an easier clue. Missing clips return an error instead of falling back to another difficulty. Redemption locks the student's row before checking their balance, preventing concurrent purchases from spending the same points.
- **Schema changes.** `010_profile_icons.sql` adds profile icon storage, and `011_icon_points_spent.sql` records redemption costs. Store balances are calculated from earned game points minus recorded spending rather than maintained as a separate balance.
- **Audio storage.** Basic retains its existing paths; Advanced and Expert use difficulty folders. #202 validates MP3 content and saves through a temporary file so a failed upload preserves the old clip. Photo and audio uploads share a bounded request-body reader.
- **Known debt.** Teacher uploads currently replace shared Basic clips; per-class ownership and difficulty-aware uploads need follow-up. Leaderboards total completed games in the class's language rather than games directly linked to that class. Shared database-error handling still comes from `teacher_access.py`. Badge sprite positions need re-measuring if the artwork is exported again.

## Testing and validation

The results below are recorded in the merged PR descriptions and existing Week 9 individual logs. They belong to different branch states and are not a single final regression run.

| Check | Environment and command | Recorded result | Execution evidence |
|---|---|---|---|
| Profile icon art and seed | Local backend with PostgreSQL; `python -m pytest tests/backend`; frontend `npm test` and TypeScript check | 703 backend tests and 128 frontend tests passed; type check clean | [#200 testing](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/200) |
| Points redemption | Local PostgreSQL; `python -m pytest tests/backend` | 655 backend tests passed, including 15 store tests | [#205 testing](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/205) |
| Store and badges frontend | Local frontend; `npm test`, `npx tsc --noEmit` and production build | 150 tests passed; type check and build passed | [#206 testing](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/206) |
| Teacher location/audio API | PostgreSQL 17 with migrations applied; backend pytest suite | 698 backend tests passed initially; 809 passed after integrating difficulty-audio changes | [Ashish's Week 9 log](../AshishNayak/week-9.md) |
| Class leaderboard API | Temporary PostgreSQL 17; backend pytest suite | 713 backend tests passed, including 10 leaderboard tests | [#217 testing](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/217) |

Also checked in tests and review:

- #198 and #200: owning and equipping icons, rejecting unowned icons, preserving the previous icon after failure, rendering known icons, unknown-icon fallback and repeatable demo seeding.
- #194 and #206: earned and locked badges, correct sprite positions, coin balance, affordable and unaffordable purchases, owned/equipped states, expired sessions and server errors. Buying and equipping were also checked in the running app, as recorded in Gamu's log.
- #196 and #204: assignment requests, class switching, listing and deleting hunts, ownership and authentication failures, empty lists and past-due filtering. Removal confirmation was checked manually.
- #202: valid uploads, invalid or oversized files, preservation of existing clips, access restrictions and database/file failures.
- #209 and #210: clue composition by difficulty, blank required text, difficulty-specific paths, missing recordings and access control.
- #212 and #215: all 18 language/difficulty combinations on the backend, invalid choices rejected before database access, and frontend selection and dashboard flow.
- #217: rankings, tied scores, equipped icons, zero-point students, exclusion of unfinished games, enrollment checks and database failures.

**CI limitation:** the individual logs report that GitHub Actions could not start jobs from November 5 because of an account billing lock. The recorded local checks support review, but do not establish a passing final CI run. The integrated application still needs a fresh regression run and manual student, teacher and admin demo checks.

## Architecture and DFD alignment

This sprint adds these data flows:

1. **Language and difficulty.** The start-game form submits both choices to `POST /api/game/start`. The backend validates and saves them, then selects locations from that language's clue pool. Existing clients retain French Basic defaults.
2. **Clue generation and playback.** The generator uses number text for Basic, numbers plus descriptions for Advanced, and descriptions for Expert. Playback uses the game's saved difficulty to find the matching recording.
3. **Badges.** The student badges page reads earned and locked badges from the existing endpoint. This exposes last week's badge-awarding work in the interface.
4. **Profile icons and points.** The store reads game points and icon spending, redemption saves ownership and cost, and equipping updates the student's selected icon. Both the store and leaderboard display that selection through the shared renderer.
5. **Class leaderboards.** The backend checks enrollment, totals completed games in the class's language and returns ranks, usernames, points and equipped icons. Equal scores share competition ranks, such as 1, 1, 3. Classes sharing a language use the same qualifying game totals for their enrolled students.
6. **Teacher hunt and content management.** The dashboard assigns, lists and removes hunts through ownership-protected endpoints. The location API lists clues in the class's language and saves validated audio to the storage read by gameplay; its upload form remains future work.
7. **Administration and documentation.** The admin screen connects teacher-email approvals and class reassignment. #193 updates the diagrams to describe session cookies, Gmail SMTP, backend PaddleOCR, GPS checks before OCR, class joining and current game flows.

## Collaboration process and next steps

The feature PRs went through teammate review, and dependent work was merged in sequence. The icon backend and renderer support the store and leaderboard; difficulty-specific audio generation supports playback and language/difficulty selection. Reviews caught several issues:

- a stale roster when switching classes in the teacher assignment view (#196), fixed with separate component keys
- fixed sprite percentages that would break if the icon grid changed (#200), replaced with calculations from the grid size
- the initial language/difficulty PR covering both backend and frontend (#212), split into #212 and #215 for smaller reviews
- a stray `main` token introduced during leaderboard integration (#219), fixed before merge
- teacher uploads replacing shared audio (#202), recorded as a per-class audio follow-up before exposing the upload form
- overlapping audio-storage changes in #202 and #209, resolved while preserving difficulty-aware paths and upload validation

Next we prepare for the Milestone 1 demo after reading break. Teacher content work needs a frontend upload form, difficulty-aware uploads, per-class audio ownership and adding locations. We need to review and integrate the replay-limit branch, checking its migration number against the merged icon-store migration. Audio descriptions also need review: LIB 312 and LIB 317 currently share an Expert description, and each selectable language needs enough locations and recordings. We still need to link assigned hunts to games, check GPS and OCR on real phones on campus, and run the full regression suite and complete demo paths on the integrated application.
