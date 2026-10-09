# Week 5 Individual Log: Gamu

Team 7 | Repo: capstone-project-team-7 | PRs this week: #43 (password hashing) merged into dev; # () merged into dev

---

## PR #43: Secure password hashing (branch `35-encrypting-user-passwords`, into `dev`)

**Size:** 4 files changed, +35 / -1 lines (`src/backend/utils/passwords.py` added, `tests/backend/test_hash_passwords.py` added, `src/backend/requirements.txt` updated).

- As part of the account/authentication requirement (task #35), passwords must never be stored as plain text in our PostgreSQL database. Since the team dropped Firebase, our own signup, login and password change code needs a safe way to hash and check passwords.
- Therefore, I implemented `hash_password(password)` in `src/backend/utils/passwords.py`, which turns a plain password into a bcrypt hash with a random salt, and `verify_password(password, hashed_password)`, which checks a typed password against a stored hash and returns True or False. I also added `bcrypt` to `requirements.txt` so CI and teammates install it.

**Review receipts**

- When I reviewed my first version, I placed `passwords.py` in `src/utils/`, but `pytest.ini` has `pythonpath = src/backend`, so the tests could not import it. Therefore, I moved it to `src/backend/utils/`, which is still inside `src/` and avoids editing the shared `pytest.ini`.
- When I reviewed `hash_password`, I noticed bcrypt only reads the first 72 bytes of a password. I did not add a length check here because password rules belong to signup and password change, so I brought it up with my team instead of editing their code. The check was then implemented in PR #45 (teacher signup, #36): passwords must be at least 8 characters and at most 72 UTF-8 bytes, and anything outside that is rejected with a 422 before it reaches the database or `hash_password`.
- Hashing, not encryption, was chosen on purpose: a hash cannot be turned back into the original password, so a leaked database does not expose real passwords.
- The PR contains two functions, each under 10 lines, and no workarounds or temporary code.

**Architecture receipts**

- `passwords.py` is in `src/backend/utils/` because the PR rules say utility files go under `src/`, and `pytest.ini` points Python at `src/backend`, so the same import style as `main.py` works. The test is in `tests/backend/` as required.
- In the DFD, this sits inside the backend authentication process. On signup and password change, the plain password goes through `hash_password` and only the hash is saved in PostgreSQL. On login, `verify_password` compares the typed password with the stored hash. Plain passwords are never written to the database.
- No existing code was edited. Signup (#32), login (#33) and password change (#34) can import these functions directly.

**Clean Code Check**

- I re-read both functions and the tests for hardcoded values, duplicate code, dead code, deep nesting and unrelated responsibilities. Each function does one job, the file is short, and there is no duplicated or dead code.

**Testing receipts**

- Happy path: `test_verify_password_correct` hashes a password and confirms `verify_password` returns True for the same password.
- Negative case: `test_verify_password_incorrect` confirms `verify_password` returns False for a wrong password.
- Extra checks: `test_hash_is_not_plaintext` confirms the stored value is not the real password, and `test_same_password_hashes_differ` confirms the random salt works.
- These are unit tests. Integration tests are not required yet because the users table and the signup/login endpoints belong to other PRs.
- Tests are in `tests/backend/test_hash_passwords.py`.
- Regression: no existing files were changed apart from adding one line to `requirements.txt`. Backend CI run: [CI run](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/37566144985/job/112614196375?pr=43)


## PR #49: Admin reassigns a class to another approved teacher (branch `42-admin-reassign-a-class-to-a-different-teacher`, into `dev`)

**Size:** 3 files changed, +195 / -0 lines (`src/backend/admin.py` added, `tests/backend/test_admin.py` added, `src/backend/main.py` updated with 2 lines).

- As part of the admin requirement (task #42), an admin must be able to move a class from one teacher to another. In the event a teacher leaves the school, so reassigning keeps the class, its enrollments and student progress safe.
- Therefore, I implemented `PATCH /api/admin/classes/{class_id}/teacher` in `src/backend/admin.py`. It takes a `teacher_email`, checks that the new teacher has a teacher account and is on the approved teacher email list, and then changes only `classes.teacher_id`. I also added `require_admin`, which only lets requests with a valid, unexpired admin session through (401 if not logged in, 403 if not an admin).

**Review receipts**

- I used the teacher's email instead of their id in the request, so an admin does not need to know internal ids. The email is trimmed and matched without caring about upper or lower case, because the users table already treats emails that way.
- The new teacher is checked before the update runs, so an unapproved teacher gets a 400 "Invalid teacher" and the class is left unchanged. A missing class gets a 404.
- The update only touches `teacher_id`. Enrollments point at the class and not at the teacher, so students keep their class and progress.
- Database errors return a clear 503 instead of crashing the app.
- `require_admin` reuses the login code's `SESSION_COOKIE` and the `sessions` table, so I did not need to edit any of the login code.
- The file is short (68 lines), each function does one job, and there is no temporary code.
- [Add feedback from your reviewer and what you changed. Add any PRs you reviewed for teammates, with the PR number and what you found.]

**Architecture receipts**

- `admin.py` is a new FastAPI router in `src/backend/`, the same style as the auth router, and the test is in `tests/backend/` as required. The only existing file I touched is `main.py`, with one import and one `app.include_router(...)` line.
- In the DFD, this sits inside the backend admin process. The admin's request carries a session cookie, `require_admin` checks it against the `sessions` and `users` tables, then the endpoint looks up the new teacher in `teachers` and `authorized_teacher_emails`, and updates one row in `classes` in PostgreSQL. Nothing else is written.
- It uses the shared `get_connection()` from `database.py` and the existing tables, so no new migration was needed.

**Clean Code Check**

- I re-read `admin.py` and the tests for hardcoded values, duplicate code, dead code, deep nesting and unrelated responsibilities. The file is short and the two main pieces (`require_admin` and `reassign_class`) each do one job. The SQL has comments explaining the two rules (approved teacher, only the teacher changes). All files are well under 500 lines.

**Testing receipts**

- Happy path: `test_admin_reassigns_class_to_approved_teacher` confirms an admin gets a 200 and the new teacher's id back.
- Negative cases: `test_unapproved_teacher_is_rejected_and_class_unchanged` confirms a 400 and that no `UPDATE` query ever runs. `test_only_logged_in_admins_can_reassign` confirms no session gives 401 and a teacher session gives 403.
- Integration: `test_reassign_against_database` uses the real PostgreSQL database. It checks that an unapproved teacher is rejected, that the email match ignores upper or lower case, that the class really moves to the new teacher, and that the student's enrollment is still there. It cleans up its test data and is skipped if `DATABASE_URL` is not set.
- The first three tests use a small fake database connection, so they run anywhere, including CI.
- Tests are in `tests/backend/test_admin.py`.
- Regression: the only existing file changed is `main.py` (2 lines added). Backend CI run: [ADD CI RUN LINK]