### Week 5 — Madiba Burks Magara

October 5–11, 2026

Merged this week: [PR #55 — Student Signup Schema](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/55), [PR #61 — Implement student registration service](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/61), and [PR #67 — Add student registration API endpoint](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/67). All three were merged into `dev`.

The test results below are recorded results from the PR descriptions and GitHub checks, rather than a fresh run of the merged `dev` branch for this report.

---

### For PR #55 — Student Signup Schema

- [x] Our student account creation requirement in issue #32 needs signup details checked before an account can be saved. I added `StudentSignupRequest` in `src/backend/schemas.py` for email, password, first name, last name, student number, and username.
- [x] I made all six fields required and rejected missing, blank, and incorrect input types. I used Pydantic's strict validation and rejected unexpected fields, including a client-supplied role, so a student cannot request an admin or teacher role through the signup payload.
- [x] I trimmed names, usernames, and student numbers, and validated email format. Usernames have a 50-character limit and student numbers have a 30-character limit. Student numbers remain strings so leading zeroes are preserved.
- [x] I required passwords to contain at least eight characters and at most 72 UTF-8 bytes to match the shared bcrypt helper. I rejected whitespace-only passwords while preserving spaces in valid passwords. The password is excluded from the model's representation, and validation errors hide input values in their text representation.
- [x] I added the email validation dependency and documented the signup rules in the README. I also changed the PostgreSQL image used by CI to Google's Docker Hub cache to address image pull limits.
- [x] I kept validation separate from database persistence and the API route. This PR checks input; the next two PRs add account creation and expose it through FastAPI.
- [x] The final PR had 123 additions and 2 deletions across five files. It stayed below the 500-line limit, and the validation rules use shared field definitions and two small validators rather than repeated checks in route handlers.
- [x] Gamu (`gamurrrrr`) requested normalization of the entire email address because email validation alone only normalizes the domain. Ashish (`nayakashish`) agreed. I added a lowercase email validator and tests showing mixed-case addresses normalize to the same value.
- [x] Ashish also suggested considering name length limits and shared validation with teacher signup. The merged schema does not add name length limits; comparison with teacher signup remains a possible follow-up. Ashish, Dan (`danruk`), and Gamu approved the PR after the email normalization change.
- [x] In the authentication DFD, this work belongs to the Backend API process that receives student account details before passing valid data to the SQL data store.

For Tests:

- [x] I added `tests/backend/test_signup_schemas.py` with positive cases for valid input, trimmed profile details, preserved password spaces, leading zeroes in student numbers, and accepted password boundaries.
- [x] The negative cases cover missing fields, blank values, incorrect types, invalid emails, short or oversized passwords, oversized usernames and student numbers, and attempts to supply a role.
- [x] I added three email case-variant cases after review. The original focused run recorded 46 passing cases before these additions.
- [x] My initial broader backend run recorded 90 passes and one failure because the local `users` table lacked the `password` column. I did not treat that run as fully passing; the local database needed its schema updated.
- [x] GitHub's [CI run for #55](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/38018392693) shows successful backend and frontend checks on the final PR commit.

---

### For PR #61 — Implement student registration service

- [x] After validating signup details, issue #32 needs the backend to save the account. I added `src/backend/registration.py` with `create_student()` to create the shared user record and its student profile in PostgreSQL.
- [x] I reused the team's `hash_password()` helper so the database stores a bcrypt hash rather than the submitted password. The service assigns the `student` role itself and returns account details without the password hash.
- [x] I created the `users` and `students` rows in one transaction. Both records are committed together, and a failed student insert rolls back the user insert so an incomplete account is not left behind.
- [x] I normalized email addresses and trimmed profile details before storage. I used parameterized SQL and the existing database connection helper rather than adding a separate connection setup.
- [x] I handled duplicate email addresses, usernames, and student numbers using the existing database uniqueness constraints. Recognized conflicts become `DuplicateStudentAccount` errors that identify the field internally. The database constraints also protect against two concurrent requests creating the same account.
- [x] I documented the service in the README and kept HTTP response handling for the endpoint PR. This service works with the existing account tables and does not require a new migration.
- [x] The final PR had 172 additions and no deletions across three files. The service module is 44 lines overall, and its work stays focused on hashing, account persistence, and duplicate handling. The tests share fixtures for account details and temporary database setup.
- [x] Gamu approved the transaction approach and concurrent-signup test, and requested clearer PR references and removal of an empty template from the description. I updated the README to remove temporary PR-stage wording and moved registration documentation into the Backend API section. The fetched PR description still contains an extra empty template, so that cleanup is not recorded as complete. Dan also approved the service's scope.
- [x] In the DFD, this work connects the Backend API account creation process to the SQL data store, using the `users` and `students` tables added in Week 4.

For Tests:

- [x] I added PostgreSQL integration tests in `tests/backend/test_registration.py`. Each test uses a temporary schema with migrations applied, and the schema is removed afterward.
- [x] The positive cases check that user and student records are committed, the role is `student`, the saved hash verifies against the submitted password, normalized details are stored correctly, and returned account details exclude the password.
- [x] The negative cases check duplicate emails, usernames, and student numbers without partial account creation. A duplicate student number exercises rollback after the user insert. Another case rejects a client-supplied role.
- [x] I tested concurrent duplicate signup and checked that only one user and one student profile remain. I also added compatibility cases passing the validated signup schema into the service, including passwords at the bcrypt byte limit.
- [x] The PR records six passing service cases and 51 passing backend cases before the compatibility additions. The combined schema and service run then recorded 58 passing cases. These are separate recorded runs, not totals to add together.
- [x] GitHub's [CI run for #61](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/38078784706) shows successful backend and frontend checks. The PR also records a passing `git diff --check`.

---

### For PR #67 — Add student registration API endpoint

- [x] I completed the backend signup flow for issue #32 by adding `POST /api/auth/student/signup` in `src/backend/student_signup.py` and registering its router in `src/backend/main.py`.
- [x] I connected the existing `StudentSignupRequest` validation to `create_student()`. FastAPI rejects invalid requests with status 422 before the registration service runs.
- [x] Successful signup returns status 201 with the new account UUID and `role: "student"`. I added a response model that limits the API response to those fields.
- [x] Duplicate account details return status 409 with `{"detail": "Account details already in use"}`. This message avoids revealing which email, username, or student number is already registered.
- [x] Database and configuration failures return status 503 with `{"detail": "Database unavailable"}`. The warning logged by the route does not include connection details or submitted credentials.
- [x] I documented the request fields and response codes in the README and added OpenAPI response descriptions. Signup creates the account without issuing a login session; navigation to login remains frontend work.
- [x] I reused the signup schema, registration service, database helper, and password hashing rather than duplicating their logic in the route. The PR included the schema and dependency needed by the endpoint while the schema PR was still awaiting merge.
- [x] The final PR had 168 additions and 5 deletions across six files. The endpoint module is 34 lines overall, and its handler delegates persistence to the service and translates errors into HTTP responses.
- [x] Dan approved the endpoint's use of the existing authentication patterns. Ashish approved the generic duplicate-account message and reported that the tests passed for him, including edge cases.
- [x] In the authentication DFD, this endpoint receives student signup requests from the frontend, validates them in the Backend API, and uses PostgreSQL to create the account. It provides the API connection between the first two PRs and the future signup page.

For Tests:

- [x] I added `tests/backend/test_student_signup.py` using FastAPI's `TestClient` and the registration tests' temporary database fixture.
- [x] The positive integration case checks status 201, the UUID and student role response, normalized stored details, a verifiable password hash, and the absence of a login cookie.
- [x] Duplicate email, username, and student number cases check status 409, the generic error message, and that only the original account remains in both tables.
- [x] Missing fields, invalid emails, short or oversized passwords, blank names, oversized identifiers, and a supplied admin role return status 422. These tests fail if invalid input reaches the registration service.
- [x] Simulated database and configuration failures check the safe status 503 response. An OpenAPI test checks the request schema and documented 201, 409, 422, and 503 responses.
- [x] The PR records 29 passing focused endpoint and service cases, followed by 174 passing cases in the broader backend run with the signup schema tests and freshly migrated temporary database schemas. It also records a passing whitespace check.
- [x] GitHub's [CI run for #67](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/38113078045) shows successful backend and frontend checks.
- [ ] I still need a fresh combined verification of the merged `dev` branch and the frontend signup-to-login flow. The linked CI runs provide evidence for the individual PR checks.

---

## How this fits the overall system

These three PRs build on my Week 4 PostgreSQL connection and account tables to implement student registration. The schema checks incoming details, the service hashes the password and saves both account records together, and the endpoint exposes that work through FastAPI. They reuse the team's password hashing and backend authentication approach. Students can then use the separate login feature to start a session. Next, we can connect the frontend signup page and verify registration, login, and current-user lookup together against PostgreSQL.
