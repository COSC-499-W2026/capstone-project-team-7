# Week 12 Individual Log: Gamu

Team 7 | Repo: capstone-project-team-7 | PRs this week: #275 (harder Polyglot Legend), #279 (teacher class report, part 1), #280 (hardest levels and CSV export, part 2), #282 (demo teacher report screen), #276 (demo teacher signup) and #284 (demo teacher class leaderboard), all merged into `main` on November 27.

I worked on the teacher side of progress tracking. Teachers can now get a per-student report for their class, see which levels were hardest, and download it all as a CSV. I also built plain demo screens for the M1 video: the report, teacher signup and a class leaderboard on the teacher dashboard.

CI note: GitHub Actions is still locked by the billing issue, so every CI run fails after 1–2 seconds without running a test. Test results below are from my own machine.

Screenshots of the UI for each frontend PR are in the PR descriptions on GitHub.


---


## PR #275: Make Polyglot Legend harder and group badges by language (branch `273-make-polyglot-badge-slightly-harder`, into `main`), merged

**Size:** 4 files changed, +88 / -19 lines.

- Polyglot Legend was too easy: it only needed one finished game in every language, on any difficulty, so a student could earn it playing Basic only. Badges also came back in no clear order (task #273).
- Therefore, Polyglot Legend now needs a finished game on Basic, Advanced and Expert in every language, and badges are grouped by language with Polyglot first.

**Review receipts**

- I kept the badge id as `polyglot`, so students don't lose a badge they already earned (although noone would have earned the badge yet as right now it is impossible)
- Limitation: only French locations are seeded, so the badge can't be earned by playing locally yet. The tests cover the rule.


**Architecture receipts**

- The badge order is set in one place, `all_badges()`.

**Testing receipts**

- New tests for each case, including a quit Expert game not counting. 948 backend and 238 frontend tests passed.

![Backend badge tests](screenshots/week-12/backend%20badges.png)


## PR #279: Teacher class report: per-student summary (branch `277-teacher-dashboard-reports`, into `main`), merged

**Size:** 5 files changed, +188 lines.

- The client wants teachers to see each student's progress, and there was no endpoint for it (task #277).
- Therefore, `GET /api/teacher/classes/{class_id}/report` returns one row per student: points, difficulties, games, times, locations completed and skipped, and plays per clue.

**Review receipts**

- It counts the same games as the class leaderboard (finished, in the class language, by enrolled students), so the numbers match.
- Skipping a clue used to delete its play count. This came from my own review on Dan's #263, where I asked for plays to reset on a skip so they don't carry over to the new room. Resetting meant the report lost them, so I now save them in `skipped_location_listens` first. Limitation: skips from before this change have no saved count, so they show as 0.

**Architecture receipts**

- The rows come from a plain helper, so part 2 reuses it for the CSV.

**Testing receipts**

- 5 tests, including a quit game and a Spanish game being left out, and 401/403/404 access checks. 950 backend tests passed.

![Teacher report tests](screenshots/week-12/teacher%20report%20tests.png)


## PR #280: Teacher class report: hardest levels and CSV export (branch `278-hardest-levels-and-export-csv`, into `main`), merged

**Size:** 4 files changed, +243 / -39 lines.

- Teachers need to see which levels students struggle with and keep the report outside the app (task #278).
- Therefore, the report now lists the most skipped, most replayed and most attempted levels, and `.../report.csv` downloads it all.

**Review receipts**

- A level is a room on one difficulty, because the same room is much harder on Expert than on Basic.
- CSV text starting with `=`, `+`, `-` or `@` gets a `'` in front, so Excel won't run it as a formula.
- Bug I fixed: the CSV file name was wrong in two ways. The class name "French 101 - Section A" became `French-101---Section-A`, because my regex kept dashes. And the date came from the server clock, which runs in UTC, so in BC evenings it showed tomorrow's date. I now collapse anything that isn't a letter or digit into one dash, and ask Postgres for today's date in Vancouver time.
- Each list shows only the top 5 levels, because with real data the lists grew to every room ever played.
- Ashish requested changes: every clue is played at least once and every found room has at least one photo, so the totals mostly show how often a room was picked, not how hard it was. He suggested counting only extra plays and attempts (`GREATEST(x - 1, 0)`), like `utils/completed_locations.py` already does for students. I fixed it: replays count plays after the first, and attempts count only wrong photos. 
- Limitation: locations have no name column, so levels are shown by building and room only.

**Architecture receipts**

- One shared game rule, `CLASS_GAMES`, is used by both the student rows and the hardest levels. No new library.

**Testing receipts**

- Tests check the exact order of all three lists, Ashish's example (a room found first try in 5 games isn't listed), the top-5 cap, the CSV contents and access checks. 960 backend tests passed.
- I ran Ashish's example test on the old code first, and it failed, so it really checks the fix.
- My first top-5 test failed with a database `CheckViolation`, because I put 7 rooms in one game and a game can only have 5 spots. I split it into two games.

![Hardest levels and CSV tests](screenshots/week-12/hardest%20levels%20csv%20tests.png)


## PR #282: Demo teacher class report screen (branch `281-demo-frontend-teacher-reports`, into `main`), merged

**Size:** 5 files changed, +307 lines.

- The report endpoints from #279 and #280 had no screen, so we couldn't show them in the M1 video (task #281).
- Therefore, a **View report** button on the teacher dashboard opens the report, with the student table, hardest levels and a **Download CSV** button.

**Review receipts**

- The first version looked squished: the shared page style is 720px wide, which is too narrow for a 10-column table. I widened only this page and made the table scroll sideways on phones. I used inline styles in my own file instead of editing the shared `style.css`, so I didn't change teammates' pages.
- It first targeted the #280 branch, so the diff only showed this screen. After #280 merged, I pulled `main` into it and it went into `main`.
- Limitation: plain demo styling only, to be redone in Milestone 2.

**Architecture receipts**

- I split it into a page that loads the data and a view that only draws it, so the view can be tested without a browser. Only 5 lines changed in an existing file.

**Testing receipts**

- 7 new tests (rows, readable times, hardest levels, empty class, errors, CSV). 245 frontend and 958 backend tests passed, and I checked it by hand with a local database.

![Report frontend tests](screenshots/week-12/report%20frontend%20tests.png)


## PR #276: Demo teacher account signup (branch `274-demo-teacher-account-creation-frontend`, into `main`), merged

**Size:** 3 files changed, +91 / -10 lines.

- For the demo, there was no way to create a teacher account from the app (task #274).
- Therefore, the create-account page has an "I'm a student" / "I'm a teacher" choice, so an email the admin approved can become a teacher account.

**Review receipts**

- This PR first also had the class leaderboard (10 files), so I split that into #284 to keep one feature per PR.
- Limitation: an approved teacher email can still sign up as a student, and can't switch afterwards, perhaps something to discuss later as a team.

**Architecture receipts**

- Frontend only. It uses the existing teacher signup endpoint.

**Testing receipts**

- 6 new tests, including the 403 message for an unapproved email. 244 frontend and 943 backend tests passed.


## PR #284: Demo teacher class leaderboard (branch `283-demo-teacher-class-leaderboard`, into `main`), merged

**Size:** 7 files changed, +173 / -3 lines.

- Teachers couldn't see their class leaderboard, only students could (task #283, split out of #276).
- Therefore, the teacher dashboard shows the leaderboard of the selected class.

**Review receipts**

- Only the teacher who owns the class can see it.
- It conflicted with `main` after #279 merged, because both added a router line in the same spot in `main.py`. The fix was to keep both lines.
- Limitation: Ashish noticed the leaderboard doesn't refresh when the roster changes. We agreed to leave it for Milestone 2, when the teacher dashboard is restructured.

**Architecture receipts**

- It reuses the student leaderboard's ranking, so teachers and students see the same ranks.

**Testing receipts**

- 8 backend tests (including another teacher's class getting 404) and 7 frontend tests. 951 backend and 245 frontend tests passed.


## Code reviews for teammates

**PR #286: Table and file storage for teachers' own location clips (Ashish)**

- I approved, and pointed out that `game_session_locations.clip_id` only references the clip's id, so a game could save a clip recorded for a different room. `hunt_clips` already blocks this with a composite key, so I suggested doing the same here.

**PR #288: Teacher API for their own clips (Ashish)**

- I approved, and flagged for the later hunt-clips PR that retiring a clip leaves its `hunt_clips` rows, so game start would need to skip retired clips.


**PR #294: Play teacher-chosen clips in hunts (Ashish)**

- I agreed with Dan's requested change: after an admin reassigns a class, the new teacher could see the old teacher's private clip labels. I suggested the fix (`AND clip.created_by = %s` with the teacher's id) and a reassignment test, and Ashish added both. I also flagged that an old hunt still plays the previous teacher's clip, which seemed fine.

**PR #296: Teachers choose clips in the assign hunt form (Ashish)**

- I approved, and asked Ashish to pull in Dan's privacy fix from #294 before merging. I also suggested a note that a chosen clip only plays if its room is one of the student's 5 random rooms, and reloading clips after one is added in My clips.

