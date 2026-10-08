# Week 5 Individual Log: Dan Rukundo

### Teacher account creation endpoint — issue #36

Work completed on branch `36-teacher-account-creation-endpoint`. PR number, reviewer feedback, and merge status are not recorded here yet.

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

## How this fits the overall system

Teacher signup connects the backend account creation process to PostgreSQL's authorized email list and account tables. It establishes the teacher role for later login and class authorization work. Shared password hashing is reused, and class management is kept outside this PR's scope.
