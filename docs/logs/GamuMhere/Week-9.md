# Week 9 Individual Log: Gamu

Team 7 | Repo: capstone-project-team-7 | PRs this week: #194 (badges page), open and waiting for review, not merged yet; 

Last week I added the badge rules and the badges endpoint, but students still had no way to see their badges in the app. This week I added a simple badges page so students can see which badges they've earned, which ones are still locked, and what each one is for. Like the other demo pages, I kept it plain on purpose, since the team agreed to finish the working features first and style everything later in Milestone 2.

---


## PR #194: Badges page (branch `190-demo-frontend-badges-page`, into `main`), open, not merged yet

**Size:** 7 files changed, +200 / -3 lines (`src/frontend/src/pages/BadgesPage.tsx`, `src/frontend/src/api/badges.ts`, `src/frontend/src/assets/badges.png` and `tests/frontend/badges.test.ts` added; `src/frontend/src/App.tsx`, `src/frontend/src/pages/StudentDashboard.tsx` and `README.md` updated).

- Badges were being earned and saved during games (my #161 and #163), but the student dashboard only had a disabled "Badges" button under "Coming soon", so students couldn't see them (task #190).
- Therefore, I replaced that button with a working **My badges** button. It opens a page that shows every badge in a grid, with "You've earned X of Y badges" at the top. Earned badges are in full colour, and locked badges are greyed out and faded with a lock, matching the badge mockups from last week.
- Hovering over a badge shows its name and what it's for (e.g. French First hunt: "Complete a full game in French on any difficulty"). Clicking or tapping a badge shows the same text under it.

**Review receipts**

- All 31 badge pictures are in one sprite sheet (`badges.png`, 5 columns × 7 rows) instead of 31 separate images, to keep the PR under our file limit. Each badge shows its part of the sheet using CSS `background-position`, and one small helper (`badgeTile`) turns a badge id like `es_advanced` into its row and column.
- A badge that isn't in the sheet (e.g. a language added later, since badges come from the `languages` table) shows a plain box with its name instead of breaking the page.
- I added click/tap as well as hover for the descriptions, because students will mostly use phones during the hunt, and phones can't hover.
- The descriptions are written in the frontend from the badge id, so I didn't need to change the backend. They match the rules in `src/backend/badges.py`
- If the login session has ended (401), the student is sent back to the login page, the same as the other pages.
- The PR is exactly at our 200-line target, so I shortened the tests by grouping related checks rather than going over.

**Architecture receipts**

- Same pattern as my other pages: the page calls `api/badges.ts`, and only that file talks to the backend (copied from the style of `api/profile.ts`). `App.tsx` decides which screen to show, with one new switch for the badges page.
- I reused the existing `SessionEndedError` and the shared `utils/languageName.ts` instead of writing new versions.
- This fits the DFD from last week's badges endpoint, so the diagram doesn't change: the student's request carries their login cookie, `require_student` checks it, and the badges process reads `student_badges` for that student only.
- I didn't change any backend code. In `StudentDashboard.tsx` and `App.tsx` I only added what was needed to open the page.

**Clean Code Check**

- Each helper does one thing: `badgeTile` (id → row and column), `badgeStyle` (colour or grey), `badgeDescription` (what it's for) and `earnedText` (the count). The page is about 100 lines. 

**Testing receipts**

- `badges.test.ts` (6 tests): loads the badge list from the right endpoint; a 401 throws `SessionEndedError` so the app goes to login; other failures show "Could not load your badges"; badge ids point to the right tile (`fr_first_hunt` 0,0, `es_advanced` 1,2, `ko_master` 5,4, `polyglot` 6,0) and an unknown id gets no tile; locked badges are grey and faded but earned ones aren't, and the count is right; and each badge type has the right description.
- The tests fake the backend's replies, so they run anywhere, including CI.
- Clicking a badge to show its description was checked by hand in the browser.
- Regression: the full frontend suite passed (128 tests), and type checking and the build pass. CI run: [CI Run](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/41898997090)

**Screenshots**

![My badges button on the student dashboard](screenshots/week-9/badges-button.png)

*The student dashboard with the new My badges button.*

![Badges page](screenshots/week-9/badges-grid.png)

*The badges page: earned badges in colour, locked badges greyed out with a lock.*

![Clicking a badge](screenshots/week-9/badge-click.png)

*Clicking a badge shows how it is earned.*

![Hovering over a badge](screenshots/week-9/badge-hover.png)

*Hovering over a badge also shows how it is earned.*


## Code reviews for teammates


