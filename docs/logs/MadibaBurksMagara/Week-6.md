### Week 6 — Madiba Burks Magara

October 12–18, 2026

Merged this week: [PR #93 — Add authenticated password changes and revoke sessions](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/93) and [PR #96 — Add password reset email requests via Gmail SMTP](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/96), both into `main`. I also implemented reset completion for [issue #97](https://github.com/COSC-499-W2026/capstone-project-team-7/issues/97) on `97-complete-password-reset`.

Merge status and change sizes below come from local Git history. Test coverage was checked against the test bodies at the referenced commits. Recorded test runs are identified separately; inspecting a test is not a new execution result. Reset completion is present at `be63701`, but its merge is not confirmed in the available `origin/main` history.

---

### For PR #93 — Add authenticated password changes and revoke sessions

- [x] The password-management requirement includes changing a password while logged in. I added `POST /api/auth/change-password` in `src/backend/password_change.py` and registered the router in `main.py`.
- [x] I reused `auth.current_user` to identify the signed-in account rather than accepting a user ID from the request. Missing or invalid sessions return 401. The request accepts the current password and a new password, and rejects unexpected fields.
- [x] I verified the current password before making changes. An incorrect current password returns 403. The new password must contain at least eight characters, cannot be all whitespace, and must fit within bcrypt's 72-byte UTF-8 limit. Valid spaces are preserved.
- [x] I moved the repeated blank-password and byte-limit checks into `utils/passwords.py` and reused them from the signup schema and password-change request. I reused the existing bcrypt hashing and verification helpers.
- [x] I updated the password and deleted all sessions for the account in one transaction. The response clears the session cookie and asks the user to log in again. If session deletion fails, the password update rolls back as well.
- [x] I added a row lock to login and locked the account during password replacement. This prevents a login using the old password from creating a session that survives the password change.
- [x] The merged change has 191 additions and 7 deletions across seven files: 198 changed lines. It adds no dependencies or migrations and documents the endpoint in the README.
- [x] Ashish's Week 6 log records approval of the change and specifically identifies the login lock as necessary for concurrent login safety. I have not treated that review statement as a new test run for this report.
- [x] An earlier version was pushed directly to `main`. I reverted it through [#90](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/90) and reintroduced it through #93 so it could receive normal PR review.
- [x] In the authentication DFD, this work belongs to the Backend API's account-management process. It reads the current account and updates the password and session records in PostgreSQL.

For Tests:

- [x] I checked the merged [`tests/backend/test_password_change.py`](https://github.com/COSC-499-W2026/capstone-project-team-7/blob/56e38cb/tests/backend/test_password_change.py). Its unit cases cover student, teacher, and admin requests, password hashing, session deletion, and secure cookie clearing.
- [x] `test_wrong_current_password_changes_nothing` checks 403 for incorrect and oversized current passwords, with no update or cookie clearing. Validation cases reject missing fields, invalid types, blank or oversized new passwords, and client-supplied user IDs.
- [x] `test_change_against_postgresql` logs in through two separate browser clients. After changing the password, both sessions return 401; the database has no remaining sessions; the old password fails; and the replacement password logs in successfully.
- [x] `test_session_delete_failure_rolls_back_password` uses a database trigger to force session deletion to fail. It checks that the response is 503, the original password still verifies, and the existing session remains usable.
- [x] Database-failure unit cases check a generic 503 response without internal details. These source assertions establish the intended coverage; I am not claiming a separate fresh full-suite run at the #93 merge commit.

---

### For PR #96 — Add password reset email requests via Gmail SMTP

- [x] Forgotten-password recovery needs a way for a user to request a link through their registered email. I added `POST /api/auth/forgot-password` in `src/backend/password_reset.py`, with email validation and no login requirement.
- [x] Registered, unknown, and rate-limited addresses receive the same generic success message. The response does not disclose whether an account exists or return its reset token.
- [x] I generated a random token and stored only its SHA-256 hash in `password_reset_tokens`. Tokens expire after 30 minutes, and requesting a replacement rotates the stored hash so the earlier link no longer matches.
- [x] I initially added a one-minute resend cooldown. Review feedback pointed out that this could still allow repeated messages to one inbox, so I added a persistent limit of five emails per rolling hour. The database applies the limits atomically, and consuming a reset token does not remove the email history.
- [x] I added numbered migrations for token storage and email limits, plus configuration examples and Docker environment settings. Existing merged migrations were not rewritten.
- [x] I added `utils/mail.py` using Python's standard SMTP, SSL, and email modules. It connects to Gmail on port 465 with certificate verification and an App Password. FastAPI schedules delivery after the response; SMTP and configuration failures log a generic warning.
- [x] I configured the project mailbox, `lostintranslationubco@gmail.com`, using the ignored local `.env`. Gmail credentials were not added to source control, and no dependencies were added for email delivery.
- [x] The merged change has 247 additions across nine files, including the hourly-cap follow-up and its tests. This stays below the agreed 250-line limit.
- [x] In the DFD, this connects the authentication API, PostgreSQL token storage, and the external email service. Email contains the link needed for the separate reset-completion endpoint; requesting a link does not itself change the password.

For Tests:

- [x] I checked the merged [`tests/backend/test_password_reset.py`](https://github.com/COSC-499-W2026/capstone-project-team-7/blob/ad4dc49/tests/backend/test_password_reset.py). `test_generic_response_and_secure_email` checks the generic response, verifies that the stored hash matches the emailed token, and checks TLS configuration using a mocked SMTP server.
- [x] Invalid email payloads are rejected before database or SMTP access. Database failures return a safe 503; SMTP failures preserve the generic request response and avoid logging private error details.
- [x] `test_tokens_cooldown_rotation_and_unknown_email` uses PostgreSQL to check token lifetime, simultaneous requests, cooldown behavior, token rotation, and the unchanged response for an unknown address. Email sending remains mocked.
- [x] `test_hourly_cap_is_atomic_and_survives_token_consumption` seeds four recent attempts and submits concurrent requests for the fifth slot. It checks that only one message is scheduled, deleting the token does not clear the cap, and aging out an attempt permits another email. It also checks that a separate account has its own quota.
- [x] Separately from the automated SMTP mocks, Gmail authentication succeeded and Gmail accepted an explicitly requested test email to the project mailbox. Inbox receipt was not independently confirmed, so SMTP acceptance is not reported as proof of inbox delivery.

---

### For issue #97 — Complete password reset

- [x] I implemented `POST /api/auth/reset-password` on `97-complete-password-reset` to accept the emailed token and a replacement password without an existing login session.
- [x] I reused the existing password policy and bcrypt helper. Invalid, expired, replaced, or already-used tokens receive the same 422 message asking the user to request a new link.
- [x] I consumed the token, updated the password hash, and revoked the account's sessions in one transaction. Success clears the cookie and requires login with the new password; database failures roll back the changes and return 503.
- [x] I serialized the account update with login and checked that concurrent submissions can consume the token only once. Reset completion preserves the email-limit history and other accounts' sessions.
- [x] Commit `be63701` contains 190 additions and 11 deletions across six files: 201 changed lines. It reuses the existing reset router and tables, adds no migration or dependency, and updates the README.
- [ ] Final merge and verification alongside the combined `main` implementation remain unconfirmed in the local history used for this report. I have kept this contribution separate from the merged work above.
- [x] In the authentication DFD, this completes the return path from the emailed link to the Backend API and SQL account store. The frontend reset form remains separate work.

For Tests:

- [x] I checked [`tests/backend/test_password_reset_completion.py` at `be63701`](https://github.com/COSC-499-W2026/capstone-project-team-7/blob/be63701/tests/backend/test_password_reset_completion.py). Its PostgreSQL fixture creates accounts and tokens in temporary migrated schemas.
- [x] `test_reset_revokes_sessions_and_requires_new_password` checks accepted password boundaries, cookie clearing, old-password rejection, new-password login, token removal, and preserved email-limit data. Reusing the consumed token returns 422.
- [x] Negative cases check unknown, expired, and replaced links without changing the original password. Invalid request bodies are rejected before database access, and database failures return a generic 503.
- [x] `test_concurrent_token_use_succeeds_once` checks that simultaneous submissions return one 200 and one 422. `test_failure_rolls_back_password_token_and_sessions` forces a database failure, checks that the original password, token, and session survive, then verifies that retrying succeeds.
- [x] Additional cases check that login holds the account lock while verifying the password and that resetting one account preserves another account's session.
- [x] During development in this working session, the full backend run passed 350 tests against a disposable migrated PostgreSQL schema. After the final two regression cases were added, the focused reset-completion suite passed all 24 tests. The frontend suite passed one test. These are separate runs from the development snapshot, not a claim that the final combined `main` was rerun.
- [ ] The frontend request-email-to-reset-to-login journey still needs implementation and verification. No application tests were rerun while writing this documentation.

---

## How this fits the overall system

This work builds on my Week 5 registration features and the team's login and cookie-session authentication. A logged-in user can verify their current password and replace it, while someone who has forgotten their password can request a time-limited email link. The completion endpoint on its feature branch uses that link to replace the password without revealing account details through the request-email response. Both password update flows revoke existing sessions and require a new login.

I also reviewed Dan's location and translated-clue storage in #92. His Week 6 log records my requests for UUID coverage and less brittle language-seed assertions, the resulting changes, and my approval afterward. Those tables provide the campus-room and translation data needed for future game sessions.

Next steps are to confirm reset-completion integration, connect the password APIs to frontend forms, verify the combined account flows against PostgreSQL, and support the team's move into game sessions and clue selection. The architecture diagram's JWT label also needs alignment with the implemented session cookies.
