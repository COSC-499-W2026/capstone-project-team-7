# Week 5 Individual Log: Dan Rukundo

Team 7 | All three PRs merged into `dev`.

| PR | Work | Status |
|---|---|---|
| [#45](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/45) | Authorized teacher signup | Merged |
| [#56](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/56) | Teacher class access | Merged |
| [#58](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/58) | Admin approval of teacher signup emails | Merged |

### PR #45: Teacher account creation endpoint — issue #36

Work completed on branch `36-teacher-account-creation-endpoint` and merged into `dev`.

- The requirement is to let authorized teachers create accounts with `role="teacher"` and reject unauthorized accounts with “Error, unauthorized account”. I implemented `POST /api/auth/teacher/signup` using the existing PostgreSQL account tables and authorized teacher email list.
- The endpoint validates email, username, password, first name, and last name. It trims account details, normalizes emails to lowercase, rejects blank names and usernames, and requires passwords to contain at least 8 characters and at most 72 UTF-8 bytes.
- I reused the existing bcrypt `hash_password()` helper so passwords are stored as hashes. The endpoint creates the `users` and `teachers` records in one transaction, preventing a failed teacher insert from leaving a partial account.
- Successful signup returns HTTP 201 with the account ID and teacher role. Unauthorized signup returns HTTP 403 with the required error message. Duplicate identities return HTTP 409, invalid inputs return HTTP 422, and database failures return HTTP 503 without exposing connection details.
- The implementation was split into `src/backend/teacher_signup.py` and a router registration in `main.py`. Tests belong in `tests/backend/test_teacher_signup.py`, and the README documents the request fields and responses.
- The final signup changes prepared in this session totaled **118 added lines across four files**: 68 backend lines, 34 test lines, and 16 documentation lines. Class access remains separate work; this endpoint does not issue a login session or verify email ownership.

For Tests:

- Added **9 automated cases**, all passing: eight invalid-input cases and one database-failure case. Invalid-input coverage includes malformed email, blank or oversized username, blank names, short or oversized passwords, and attempts to submit a role.
- PostgreSQL-dependent automated cases were removed to keep this PR smaller. The retained tests do not verify successful persistence.
- Separately verified the endpoint against a temporary **PostgreSQL 17** database: authorized signup persisted a teacher with a valid password hash; unauthorized signup returned the required error and created no account; duplicate signup was rejected; and a forced teacher insert failure rolled back user creation. All four checks passed.
- The temporary database and test schema were cleaned up afterward. These checks did not add files to the signup PR. The available backend suite also passed with 18 tests; database-dependent tests were skipped in that run.

Local database issue:

- Docker inspection found PostgreSQL 18 data under `18/docker` in my existing project volume, while shared Docker Compose and CI specify PostgreSQL 17. The project container failed to initialize that volume.
- I inspected the volume read-only and preserved its contents. A separate temporary PostgreSQL 17 container allowed signup verification without changing the team's Docker or CI configuration. Repairing my local database setup remains outstanding.

### PR #56: Teacher class access — issue #46

- I implemented `GET /api/teacher/classes` to return only classes assigned to the signed-in teacher and `GET /api/teacher/classes/{class_id}` to retrieve one assigned class. A teacher with no classes receives an empty list.
- The endpoints use the existing session cookie and check the hashed session token against an unexpired session in PostgreSQL. Missing, invalid, or expired sessions return 401; users with a non-teacher role receive 403.
- Both class queries filter by the authenticated teacher's ID. Another teacher's class and a missing class both return 404, preventing access to other teachers' class details. Database failures return 503 without exposing connection details.
- I kept the feature in `src/backend/teacher_access.py` and registered its router in `main.py`, using the existing database connection helper and tables.

Testing coverage:

- `tests/backend/test_teacher_access.py` covers listing only assigned classes, retrieving an assigned class, teachers with no classes, rejected roles and missing sessions, hidden classes belonging to another teacher, invalid or expired sessions, and database failures.
- The PR's checks passed before merging. Database-dependent cases use a test database; no new test run is claimed by this log update.

### PR #58: Admin approval of teacher signup emails — issue #41

- I implemented `POST /api/admin/approved-teachers`, accepting an email and returning HTTP 201 with the normalized email and `approved: true`.
- The endpoint trims and lowercases emails, rejects invalid input and unexpected fields, and inserts approved emails into the existing `authorized_teacher_emails` table. No schema migration was needed.
- Approval requires a valid, unexpired admin session. Missing, invalid, or expired sessions return 401; non-admins receive 403. Duplicate approvals return 409, invalid input returns 422, and database failures return 503.
- This connects the administrator's approval action to my teacher signup endpoint: an approved email can be used to create a teacher account. Approval itself does not create the account or assign a class.
- I kept the feature in `src/backend/teacher_approval.py`, registered its router in `main.py`, and documented the API in the README.

Testing coverage:

- `tests/backend/test_teacher_approval.py` covers approval enabling teacher signup, rejected authorization attempts leaving the approval list unchanged, missing sessions and invalid input being rejected before opening a database connection, and safe database-failure responses.
- The PR's checks passed before merging. Integration tests use `TEST_DATABASE_URL` and temporary schemas; no new test run is claimed by this log update.

## Integration and collaboration

All three PRs were approved and merged into `dev`. During integration, conflicts in `main.py` and the README required keeping both the teacher approval and admin router registrations, along with the teacher approval and current-user API documentation. These shared files need coordinated edits so integrating one feature does not remove another.

## How this fits the overall system

My three PRs connect administrator approval, authorized teacher account creation, and access to assigned classes. They reuse the team's password hashing, session cookies, and PostgreSQL tables. Together with the team's login and class reassignment features, they support the teacher account and class authorization flow in the updated system architecture.
