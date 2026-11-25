# Week 12 Individual Log: Gamu

Team 7 | Repo: capstone-project-team-7 | PRs this week: #275 (harder Polyglot Legend), #279 (teacher class report, part 1), #280 (hardest levels and CSV export, part 2), #282 (demo teacher report screen), #276 (demo teacher signup) and #284 (demo teacher class leaderboard), all open and waiting for review.

I worked on the teacher side of progress tracking. Teachers can now get a per-student report for their class, see which levels were hardest, and download it all as a CSV. I also built plain demo screens for the M1 video: the report, teacher signup and a class leaderboard on the teacher dashboard.

CI note: GitHub Actions is still locked by the billing issue, so every CI run fails after 1–2 seconds without running a test. Test results below are from my own machine.

Screenshots of the UI for each frontend PR are in the PR descriptions on GitHub.


---


## PR #275: Make Polyglot Legend harder and group badges by language (branch `273-make-polyglot-badge-slightly-harder`, into `main`), open

**Size:** 4 files changed, +88 / -19 lines.

- Polyglot Legend was too easy, and badges came back in no clear order (task #273).
- Therefore, Polyglot Legend now needs a finished game on Basic, Advanced and Expert in every language, and badges are grouped by language with Polyglot first.

**Review receipts**

- I kept the badge id as `polyglot`, so students don't lose a badge they already earned.
- Limitation: only French locations are seeded, so the badge can't be earned by playing locally yet. The tests cover the rule.

**Architecture receipts**

- The badge order is set in one place, `all_badges()`.

**Testing receipts**

- New tests for each case, including a quit Expert game not counting. 948 backend and 238 frontend tests passed.

![Backend badge tests](screenshots/week-12/backend%20badges.png)


## PR #279: Teacher class report: per-student summary (branch `277-teacher-dashboard-reports`, into `main`), open

**Size:** 5 files changed, +188 lines.

- The client wants teachers to see each student's progress, and there was no endpoint for it (task #277).
- Therefore, `GET /api/teacher/classes/{class_id}/report` returns one row per student: points, difficulties, games, times, locations completed and skipped, and plays per clue.

**Review receipts**

- It counts the same games as the class leaderboard (finished, in the class language, by enrolled students), so the numbers match.
- Skipping a clue used to delete its play count, so I now save it first. Limitation: skips from before this change have no saved count, so they show as 0.

**Architecture receipts**

- The rows come from a plain helper, so part 2 reuses it for the CSV.

**Testing receipts**

- 5 tests, including a quit game and a Spanish game being left out, and 401/403/404 access checks. 950 backend tests passed.

![Teacher report tests](screenshots/week-12/teacher%20report%20tests.png)


## PR #280: Teacher class report: hardest levels and CSV export (branch `278-hardest-levels-and-export-csv`, into `main`), open

**Size:** 6 files changed, +362 lines (includes #279's changes until it merges).

- Teachers need to see which levels students struggle with and keep the report outside the app (task #278).
- Therefore, the report now lists the most skipped, most replayed and most attempted levels, and `.../report.csv` downloads it all.

**Review receipts**

- A level is a room on one difficulty, because the same room is much harder on Expert than on Basic.
- CSV text starting with `=`, `+`, `-` or `@` gets a `'` in front, so Excel won't run it as a formula.
- Limitation: locations have no name column, so levels are shown by building and room only.

**Architecture receipts**

- One shared game rule, `CLASS_GAMES`, is used by both the student rows and the hardest levels. No new library.

**Testing receipts**

- Tests check the exact order of all three lists, the CSV contents and file name, and access checks. 958 backend tests passed.

![Hardest levels and CSV tests](screenshots/week-12/hardest%20levels%20csv%20tests.png)


## PR #282: Demo teacher class report screen (branch `281-demo-frontend-teacher-reports`, into `278-hardest-levels-and-export-csv`), open

**Size:** 5 files changed, +307 lines.

- The report endpoints from #279 and #280 had no screen, so we couldn't show them in the M1 video (task #281).
- Therefore, a **View report** button on the teacher dashboard opens the report, with the student table, hardest levels and a **Download CSV** button.

**Review receipts**

- It targets the #280 branch so the diff only shows this screen. It moves to `main` once #280 merges.
- Limitation: plain demo styling only, to be redone in Milestone 2.

**Architecture receipts**

- I split it into a page that loads the data and a view that only draws it, so the view can be tested without a browser. Only 5 lines changed in an existing file.

**Testing receipts**

- 7 new tests (rows, readable times, hardest levels, empty class, errors, CSV). 245 frontend and 958 backend tests passed, and I checked it by hand with a local database.

![Report frontend tests](screenshots/week-12/report%20frontend%20tests.png)


## PR #276: Demo teacher account signup (branch `274-demo-teacher-account-creation-frontend`, into `main`), open

**Size:** 3 files changed, +91 / -10 lines.

- For the demo, there was no way to create a teacher account from the app (task #274).
- Therefore, the create-account page has an "I'm a student" / "I'm a teacher" choice, so an email the admin approved can become a teacher account.

**Review receipts**

- This PR first also had the class leaderboard (10 files), so I split that into #284 to keep one feature per PR.
- Limitation: an approved teacher email can still sign up as a student, and can't switch afterwards.

**Architecture receipts**

- Frontend only. It uses the existing teacher signup endpoint.

**Testing receipts**

- 6 new tests, including the 403 message for an unapproved email. 244 frontend and 943 backend tests passed.


## PR #284: Demo teacher class leaderboard (branch `283-demo-teacher-class-leaderboard`, into `main`), open

**Size:** 7 files changed, +173 / -3 lines.

- Teachers couldn't see their class leaderboard, only students could (task #283, split out of #276).
- Therefore, the teacher dashboard shows the leaderboard of the selected class.

**Review receipts**

- Only the teacher who owns the class can see it. Limitation: demo only, so the README wasn't updated.

**Architecture receipts**

- It reuses the student leaderboard's ranking, so teachers and students see the same ranks.

**Testing receipts**

- 8 backend tests (including another teacher's class getting 404) and 7 frontend tests. 951 backend and 245 frontend tests passed.


## Code reviews for teammates

