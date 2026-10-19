# Week 6 Team Log: Team 7

Authors: Ashish, Dan, Gamu, Madiba

October 12–18, 2026

## PRs covered

| PR | Author | What | Status |
|---|---|---|---|
| [#76](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/76) | Ashish (nayakashish) | Teachers create classes with a language and class code | Merged |
| [#78](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/78) | Ashish (nayakashish) | Teachers add students to their classes | Merged |
| [#80](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/80) | Ashish (nayakashish) | Teachers remove students from their classes | Merged |
| [#81](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/81) | Gamu (gamurrrrr) | Admins delete teacher accounts after class reassignment | Merged |
| [#82](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/82) | Ashish (nayakashish) | Update the PR template and branch guidance | Merged |
| [#83](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/83) | Gamu (gamurrrrr) | Admins delete student accounts | Merged |
| [#84](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/84) | Gamu (gamurrrrr) | Admins create additional admin accounts | Merged |
| [#85](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/85) | Gamu (gamurrrrr) | Admins enroll students in any class | Merged |
| [#88](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/88) | Dan (danruk) | Shared Basic, Advanced, and Expert difficulty rules | Merged |
| [#89](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/89) | Ashish (nayakashish) | Students join classes using a class code | Merged |
| [#90](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/90) | Madiba (KoesOremus) | Revert a direct password-change push so it can receive PR review | Merged |
| [#92](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/92) | Dan (danruk) | PostgreSQL storage for campus locations and translated clues | Merged |
| [#93](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/93) | Madiba (KoesOremus) | Logged-in password changes and session revocation | Merged |
| [#95](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/95) | Dan (danruk) | Reuse shared authentication in teacher endpoints | Merged |
| [#96](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/96) | Madiba (KoesOremus) | Forgotten-password emails, hashed tokens, and resend limits | Merged |

Merged statuses above are supported by the locally available `origin/main` history. Reset completion is also implemented on `97-complete-password-reset` (commit `be63701`); its merge is not confirmed in that history, so it is recorded separately below.

## Goal and work distribution

- Building on last week's account and authentication foundation, our goal was to extend class and account management and begin the data foundation for the scavenger hunt.
- Ashish implemented teacher class creation, enrollment and removal, and student self-enrollment by class code (#76, #78, #80, #89). He also updated the PR template and repository guidance for targeting `main` (#82).
- Gamu implemented admin deletion of teacher and student accounts, creation of additional admins, and enrollment of students into any class (#81, #83, #84, #85).
- Dan implemented shared difficulty rules, location and translated clue storage, and the shared-authentication refactor for teacher endpoints (#88, #92, #95).
- Madiba implemented logged-in password changes and forgotten-password email requests (#93, #96), and completed reset submission on its feature branch. The reset flow validates the emailed token, changes the password, consumes the token, and revokes existing sessions.
- The merged backend now supports creating classes and managing their rosters through teacher, student, and admin workflows. Difficulty rules and clue storage provide foundations for game sessions; they do not yet constitute a running hunt.

## Code-base health

- **Shared authentication and validation.** Dan's #95 removes duplicated session handling from teacher class access and teacher approval. Protected routes reuse `auth.current_user` and role dependencies. Password changes and reset completion reuse password validation rather than maintaining different rules for each flow.
- **Authorization and data ownership.** Teacher enrollment and removal check class ownership before changing a roster. Student self-enrollment derives the student ID from the session. Admin endpoints restrict account operations by role, and teacher deletion is blocked while the teacher still owns classes.
- **Concurrent requests and transactions.** Enrollment uniqueness comes from the database, preventing duplicate rows under concurrent requests. Password changes lock the account and revoke sessions transactionally. Login uses a compatible row lock so an old-password login cannot create a surviving session during a password change. Reset completion also tests single-use token consumption and rollback on failure.
- **Password-reset privacy and abuse prevention.** Forgotten-password requests return the same message for registered, unknown, and rate-limited emails. Only token hashes are stored, links expire after 30 minutes, and persistent limits allow one email per minute and five per rolling hour. Consuming a token does not clear the hourly quota.
- **Schema and shared-file integration.** Location/clue storage and reset-token storage use new migrations. Router imports, README sections, migration numbering, and shared password helpers need checking when branches merge. A password-helper conflict should retain one shared validator, avoiding a duplicate definition.
- **Remaining cleanup.** Shared test fixtures are still imported between test modules; Gamu suggested moving them to `conftest.py` in a separate refactor. Repeated database-error handling is another possible follow-up, outside the feature PRs.

## Testing and validation

We checked test bodies in the locally available merged implementation at `56e38cb` (`origin/main`), and reset-completion tests at `be63701`. The examples below describe assertions present in those snapshots; inspecting a test does not establish that it passed in a new run.

| Area | Test evidence inspected | What the assertions establish |
|---|---|---|
| Teacher enrollment | [`test_teacher_enrolls_student_in_owned_class` and `test_already_enrolled_student_is_rejected`](https://github.com/COSC-499-W2026/capstone-project-team-7/blob/56e38cb/tests/backend/test_class_enrollment.py) | A successful request writes the expected class/student pair; repeating it returns 409 and leaves one enrollment. Missing or unowned classes return 404 with no enrollment created. |
| Student removal and self-enrollment | [`test_teacher_removes_enrolled_student`](https://github.com/COSC-499-W2026/capstone-project-team-7/blob/56e38cb/tests/backend/test_class_enrollment.py) and [`test_student_joins_class_with_code`](https://github.com/COSC-499-W2026/capstone-project-team-7/blob/56e38cb/tests/backend/test_student_enrollment.py) | Removal deletes the enrollment while preserving the student and user rows. Joining by code persists an enrollment for the signed-in student; duplicate and expired-session cases check rejection and enrollment counts. |
| Teacher deletion | [`test_delete_after_reassign_keeps_student_data`](https://github.com/COSC-499-W2026/capstone-project-team-7/blob/56e38cb/tests/backend/test_teacher_deletion.py) | Deletion returns 409 while the teacher owns a class. After reassignment it returns 204, the teacher account is absent, and the class's student enrollment remains. |
| Admin creation | [`test_new_admin_can_log_in`](https://github.com/COSC-499-W2026/capstone-project-team-7/blob/56e38cb/tests/backend/test_admin_creation.py) | An existing admin creates an account through the endpoint; a duplicate returns 409; the new account logs in with the admin role. This checks the creation-to-login flow against PostgreSQL. |
| Location and clue storage | [`test_location_supports_multiple_language_clues` and `test_deleting_location_removes_its_clues_only`](https://github.com/COSC-499-W2026/capstone-project-team-7/blob/56e38cb/tests/backend/test_database.py) | Stored translations can be read back. Deleting one location removes its clues while preserving another location's clues and the language records. These tests exercise storage, not hunt selection or audio. |
| Password changes | [`test_change_against_postgresql` and `test_session_delete_failure_rolls_back_password`](https://github.com/COSC-499-W2026/capstone-project-team-7/blob/56e38cb/tests/backend/test_password_change.py) | Both existing browser sessions become unauthorized; the old password fails and the new one works. A forced session-deletion failure leaves the original password and session usable. |
| Reset email limits | [`test_hourly_cap_is_atomic_and_survives_token_consumption`](https://github.com/COSC-499-W2026/capstone-project-team-7/blob/56e38cb/tests/backend/test_password_reset.py) | Concurrent requests compete for the fifth allowed email; deleting the token does not clear the quota; aging out an attempt permits another email. SMTP is mocked, so this does not prove inbox delivery. |
| Reset completion on its feature branch | [`test_concurrent_token_use_succeeds_once` and `test_failure_rolls_back_password_token_and_sessions`](https://github.com/COSC-499-W2026/capstone-project-team-7/blob/be63701/tests/backend/test_password_reset_completion.py) | Concurrent submissions produce one success and one rejection. A forced database failure preserves the old password, reset token, and session; retrying after removing the failure succeeds. This is branch coverage, not evidence of integration into `main`. |

**Correction carried forward from Week 5.** Merged #45 does test teacher-signup persistence. At its merge commit, [`test_authorized_teacher_signup_persists_account`](https://github.com/COSC-499-W2026/capstone-project-team-7/blob/f0ef10635e794f5749797ee1c803c09a29213128/tests/backend/test_teacher_signup.py) submits the signup request, opens a separate PostgreSQL connection, reads both `users` and `teachers`, and verifies the saved details and bcrypt hash. The same file tests unauthorized signup creating no records and duplicate signup leaving one account. The earlier statement that automated persistence tests were absent was incorrect; this is existing Week 5 coverage, not a new Week 6 contribution.

**Recorded execution and limits.** During reset-completion development, a full backend run passed 350 tests against a disposable migrated PostgreSQL schema. After two more regression tests were added, the focused completion suite passed 24 tests; the frontend suite passed one test. These were development runs from this working session, not a new verification of the final combined `main`. Other contributors' historical suite totals are omitted here because they describe different snapshots and do not establish combined regression results.

No application tests were rerun for this documentation edit. Database fixtures can skip integration cases when their required database URLs are missing, so future full-suite evidence should record the commit, environment, and skips as well as the pass count. Frontend forms and the integrated hunt remain follow-up work. Gmail accepting a test message does not independently confirm inbox receipt.

## Architecture and DFD alignment

Class creation and roster changes extend the Class Management process described in the DFD. FastAPI checks the signed-in user's role and, for teachers, class ownership before writing to PostgreSQL. Teacher enrollment, admin enrollment, and student self-enrollment all use the same `class_enrollments` table, so the roster remains consistent across entry points.

Admin account management extends the existing backend-managed authentication architecture. The initial admin still comes from the seed script; additional admins are created through an authenticated admin endpoint. Account deletion relies on database relationships to remove dependent records while preserving classes where required.

Password recovery connects the backend to Gmail SMTP over verified TLS. The backend stores a token hash and expiry, then schedules email delivery after the request response. Reset completion accepts the token and replacement password through the API and requires the user to log in again. Credentials remain in the ignored local `.env`.

The game foundation now includes shared difficulty definitions and location/clue storage. Basic exposes a room number, Advanced a number and description, and Expert a description. Translations are stored per location and language, while difficulty controls which content a future game presents. Campus data seeding, random location selection, audio, GPS, photos, and game-session behavior still need implementation.

The architecture diagram linked in Week 5 remains a design reference. Its REST/JSON-with-JWT label still needs reconciliation with the implemented cookie-session authentication. This log does not claim a new diagram revision.

## Collaboration process and next steps

The team moved PR targets from `dev` to `main` and updated the shared template and guidance. Feature work continued through small PRs with teammate review. A password-change commit pushed directly to `main` was reverted through #90 and reintroduced through the reviewed #93, restoring the intended review process.

Reviews produced concrete changes: Madiba's location-storage review led to UUID coverage and less brittle language-seed assertions; discussion between Ashish and Dan clarified the Advanced difficulty rules; and feedback on reset-email spam led to the persistent hourly cap. Dan's authentication refactor addressed duplicated session checks previously identified during review.

Next steps are to finish review and integration of reset completion, connect account and class APIs to frontend pages, and begin game-session creation and clue selection. The team also needs campus locations and translations, combined-flow verification against the integrated backend, and diagram updates reflecting cookie sessions. Future game progress must account for class-specific data cleanup when a student leaves a class.
