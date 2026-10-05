### Week 4 — Madiba Burks Magara

September 27–October 4, 2026

Merged this week: PR #27 — Connect PostgreSQL and PR #29 — Add PostgreSQL Database Schema.

---

### For PR #27 — Connect PostgreSQL

- [x] As part of our Technology Stack requirement, we need PostgreSQL connected to the backend before we can save account or game data. I set up PostgreSQL 17 in `compose.yaml` with a data volume, a health check, and a port that is only available on localhost.
- [x] I added `.env.example` and `src/backend/database.py` to make the connection setup easier for the team. The connection URL comes from the environment, and each developer keeps their local settings in an ignored `.env` file. The connection helper has a five-second timeout and can commit changes or roll them back if something fails.
- [x] I added `/api/health/db` so we can check whether the backend can reach the database. It returns `{"status": "ok"}` with status 200 when the connection works. If the configuration is missing or the connection fails, it returns status 503 with `{"detail": "Database unavailable"}`.
- [x] When I checked my work, the PostgreSQL container was healthy, Compose validation passed, and I was able to run `SELECT 1`. I added the volume for persistent storage, but I did not record a restart test to check that the data was kept.
- [x] I also added PostgreSQL to the backend CI setup and wrote instructions in the README. I updated the README to match our team's decision to handle authentication ourselves instead of using Firebase.
- [x] There is no temporary account or game logic in this PR. The health route just checks the database connection. I put the schema work in a separate PR to keep both PRs under the 500-line limit.
- [x] This PR had 227 additions and 7 deletions across 10 files. Both `get_connection()` and `database_health()` are under 15 lines, including their definitions.
- [x] I checked for hardcoded values, repeated code, unused code, unnecessary calls, too many conditions, deep nesting, and functions doing too many unrelated things. The connection code stays in one helper, and the health route only checks connectivity. The version and timeout are setup defaults, while the connection URL can be changed through configuration.
- [x] I resolved merge conflicts while keeping the team's frontend CI and DFD documentation along with my database changes.
- [ ] I still need to check the PR review history before adding reviewer names and comments to this report.
- [x] In the DFD, this work connects the Backend API process to the SQL data store. It gives the backend a way to reach PostgreSQL before we start adding features that use it.

For Tests:

- [x] I added tests in `tests/backend/test_main.py` and `tests/backend/test_database.py` using pytest and FastAPI's `TestClient`.
- [x] The positive tests check that the health route returns status 200 and the correct JSON. The database integration test runs a real PostgreSQL query and then calls the health route.
- [x] The negative tests check missing configuration and a failed connection. Both should return status 503 without showing connection details.
- [x] The local connection check, Compose validation, and whitespace checks passed.
- [ ] My first attempt to run the full backend tests stalled while loading Python dependencies, so I cannot count that attempt as a passing run. CI is set up to upload an HTML report, but I still need to verify a successful CI run.

---

### For PR #29 — Add PostgreSQL Database Schema

- [x] Our account and class features need tables for students, teachers, admins, classes, and enrollments. I added `src/backend/migrations/001_accounts_and_classes.sql` to create the first version of this database structure.
- [x] I added a shared `users` table for all three account types. It stores names, roles, unique emails and usernames, and a required password value. Emails and usernames cannot be duplicated by changing their capitalization. The password field is meant to store a salted password hash, but the backend still needs to handle hashing and login checks.
- [x] I added separate student and teacher tables, unique student numbers, teacher-owned classes, and student enrollments. I also added a teacher email allowlist, the six languages from our proposal, and a table for the languages a student studies.
- [x] I wrote `src/backend/migrate.py` so we can apply the SQL migrations in order. It keeps track of migrations that have already run, skips them when nothing has changed, and rejects edits to applied files. If a migration fails, the batch is rolled back. It also prevents migration runners from applying changes at the same time.
- [x] When I reviewed the schema, I compared it with our proposal and our decision to stop using Firebase. I checked that the constraints reject invalid roles, repeated identities, and incorrect relationships. The backend still needs to check teacher signup permission and who is allowed to access each feature.
- [x] I updated CI to run migrations and schema tests, and added setup and design notes in `docs/design/database.md`.
- [x] This PR does not add temporary login or gameplay code. It sets up the tables we need before building those features.
- [x] The merged change had 296 additions and 11 deletions across six files. The migration runner is 51 lines overall, and `apply_migrations()` is 29 lines including its definition.
- [x] I checked for the same code quality issues as in PR #27. The SQL handles the tables and constraints, while the Python runner handles applying migrations. I used shared helpers in the tests to avoid repeating account and class setup. The six seeded languages come from the proposal.
- [x] I resolved README and CI conflicts while keeping the team's documentation and frontend CI. The merged test file also keeps the database connection and health-route test from PR #27.
- [ ] I still need to verify reviewer names and any requested changes from the PR review history.
- [x] In the DFD, this work belongs to the SQL data store. These tables will hold the account and class information used by the backend.

For Tests:

- [x] I added 19 schema integration test cases in `tests/backend/test_database.py`. They use a separate temporary PostgreSQL schema, roll back the data after each test, and remove the schema at the end.
- [x] The positive cases check password-value storage for all three roles, the six languages, rerunning migrations, valid enrollment, and removing related records when an account is deleted. The password tests check storage only; they do not test hashing.
- [x] The negative cases check missing or blank passwords, duplicate emails and usernames, invalid roles, mismatched student or teacher records, students owning classes, duplicate enrollment, nonstudents enrolling, and unknown languages.
- [x] I also tested that a failed migration rolls back its changes and that changing an already applied migration is rejected.
- [x] The recorded local run passed all 19 schema cases. Before merging, the backend suite passed 21 tests: the 19 schema cases and the two existing API tests.
- [ ] I still need a fresh test run of the merged branch and a verified CI result. I also need to attach a test-output screenshot or CI report as evidence.

---

## How this fits the overall system

These two PRs give us a working PostgreSQL connection and the first account and class tables. Together with the team's FastAPI, React, Docker, and CI setup, this gives us a starting point for building the app's features. Next, we can work on account creation and login, then add the tables needed for gameplay.
