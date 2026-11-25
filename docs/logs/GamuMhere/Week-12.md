# Week 12 Individual Log: Gamu

Team 7 | Repo: capstone-project-team-7 | PRs this week: #275 (harder Polyglot Legend, badges grouped by language),#279 (teacher class report, part 1) and #280 (hardest levels and CSV export, part 2), all open and waiting for review.

I worked on the teacher side of progress tracking. Teachers can now get a per-student report for their class, see which levels were hardest, and download it all as a CSV. 

CI note: GitHub Actions is still locked by the billing issue, so every CI run fails after 1–2 seconds without running a test. Test results below are from my own machine


---


## PR #275: Make Polyglot Legend harder and group badges by language (branch `273-make-polyglot-badge-slightly-harder`, into `main`), open

**Size:** 4 files changed, +88 / -19 lines (`src/backend/badges.py`, `src/frontend/src/pages/BadgesPage.tsx`, `tests/backend/test_badges.py`, `tests/frontend/badges.test.ts`).

- Polyglot Legend was too easy, and badges came back in no clear order (task #273).
- Therefore, Polyglot Legend now needs a finished game on Basic, Advanced and Expert in every language. Badges come back with Polyglot first, then each language's 5 badges together.

**Review receipts**

- Quit games never count, since they never get `finished_at`.
- The badge id is still `polyglot`, so badges students already earned are kept.

**Architecture receipts**

- The badge order is set in one place, `all_badges()`. No badge ids changed.

**Testing receipts**

- New tests: earned when every difficulty is finished in every language; not earned with only Basic, with a missing Expert, or when the Expert game was quit; and the exact badge order.
- 948 backend and 238 frontend tests passed.

![Backend badge tests](screenshots/week-12/backend%20badges.png)

![Frontend badge tests](screenshots/week-12/frontend%20badges.png)



## PR #279: Teacher class report: per-student summary (branch `277-teacher-dashboard-reports`, into `main`), open

**Size:** 5 files changed, +188 lines (`src/backend/teacher_report.py`, `src/backend/migrations/019_skipped_clue_listens.sql` and `tests/backend/test_teacher_report.py` added; `src/backend/game_session.py` and `src/backend/main.py` updated).

- The client wants teachers to see each student's progress, and there was no endpoint for it
- Therefore, `GET /api/teacher/classes/{class_id}/report` returns one row per student: points, difficulties completed, games finished, total and fastest time, locations completed and skipped, and plays per clue.

**Review receipts**

- It counts the same games as the class leaderboard: finished games, in the class's language, by students still enrolled.
- Skipping a clue used to delete its play count. It's now saved in `skipped_location_listens` first, so the report stays accurate.
- No emails, passwords or student numbers are returned.

**Architecture receipts**

- `student_report_rows()` is a plain helper, separate from the route, so part 2 reuses it for the CSV. The route reuses `teacher_connection` and `owned_class`.

**Testing receipts**

- 5 tests: only finished games in the class language count, a skip saves its plays, removed students are left out, 401/403, and 404 for another teacher's class.
- 950 backend tests passed.

![Teacher report tests](screenshots/week-12/teacher%20report%20tests.png)


## PR #280: Teacher class report: hardest levels and CSV export (branch `278-hardest-levels-and-export-csv`, into `main`), open

**Size:** 6 files changed, +362 lines (`src/backend/migrations/020_skipped_clue_attempts.sql` added; `src/backend/teacher_report.py`, `src/backend/game_session.py` and `tests/backend/test_teacher_report.py` updated). 

- Teachers need to see which levels students struggle with and take the report out of the app for personal records
- Therefore, the report now has a `hardest_levels` section (most skipped, most replayed, most photo attempts). `GET /api/teacher/classes/{class_id}/report.csv` downloads everything as a CSV.

**Review receipts**

- A level is a room on one difficulty, so the same room on Basic and Expert counts separately.
- Text starting with `=`, `+`, `-` or `@` gets a `'` in front, so Excel won't run it as a formula.
- Skipped clues' photo attempts are now saved too (`skipped_location_attempts`), the same way #279 saves plays.

**Architecture receipts**

- The leaderboard's game rule lives in one place, `CLASS_GAMES`, used by both the student rows and the hardest levels. The CSV is built from the same two helpers with Python's `csv` module, so there's no new library.

**Testing receipts**

- New tests: exact counts and order of the hardest-levels lists, an empty class, the CSV's contents and file name, formula-safe text, a skip saving plays and attempts, and 401/403/404 on the CSV route.
- 958 backend tests passed.

![Hardest levels and CSV tests](screenshots/week-12/hardest%20levels%20csv%20tests.png)


## Code reviews for teammates

