# Week 6 Individual Log: Gamu

Team 7 | Repo: capstone-project-team-7 | PRs this week: #81 (admin deletes teacher accounts) merged into main; #83 (admin deletes student accounts) merged into main; #84 (admin adds other admin accounts) merged into main; #85 (admin adds students to classes) merged into main

---


## PR #81: Admin deletes teacher accounts after their classes are reassigned (branch `72-admin-admin-can-delete-teacher-accounts`, into `main`)

**Size:** 4 files changed, +189 / -0 lines (`src/backend/teacher_deletion.py` added, `tests/backend/test_teacher_deletion.py` added, `src/backend/main.py` updated with 2 lines, `README.md` updated with a new section).

- As part of the admin account management requirement (task #72), an admin must be able to remove a teacher who has left the school. A class belongs to its teacher, and deleting a class also deletes its student enrollments, so deleting a teacher who still has classes would wipe out student progress.
- Therefore, I implemented `DELETE /api/admin/teachers/{teacher_id}` in `src/backend/teacher_deletion.py`. It returns 204 and removes the account only when the teacher has no classes left. If any class is still assigned, it returns 409 "Reassign this teacher's classes before deleting them" and nothing is deleted. The admin then uses the reassign endpoint from #49 first.

**Review receipts**

- I chose to refuse the delete (409) instead of quietly deleting the classes along with the teacher. This matches what the team agreed: a teacher's classes must be moved to another teacher first so students never lose their class or progress.
- When I reviewed the first version, I noticed a gap: an admin could reassign a class *to* this teacher in the moment between the "does this teacher have classes?" check and the delete. Therefore, I lock the teacher row (`SELECT ... FOR UPDATE`) during the check, so nothing can be assigned to them until the delete finishes.
- Unknown teachers get 404, not logged in gets 401, non-admins get 403, and database errors give a clear 503 instead of crashing.
- I reused `require_admin` and `database_unavailable` from `admin.py` (#49) instead of writing a new login or error check. No existing lines were changed.
- Student account deletion is also part of requirement #40, but I kept it as a separate PR (#83) to keep each PR small and easy to review.

**Architecture receipts**

- `teacher_deletion.py` is a new FastAPI router in `src/backend/`, in the same style as `admin.py`, and the test is in `tests/backend/` as required. The only existing code file I touched is `main.py`, with one import and one `app.include_router(...)` line.
- In the DFD, this sits inside the backend admin process. The admin's request carries a session cookie, the shared `current_user` check (#57) and `require_admin` confirm they are an admin, then the endpoint reads `teachers` and `classes` and, if no classes remain, deletes one row from `users` in PostgreSQL. The teacher's row in `teachers` goes with it through the existing cascade.
- It works together with the reassign class endpoint (#49): reassign first, then delete. No new migration was needed.

**Clean Code Check**

- I re-read the file and tests for hardcoded values, duplicate code, dead code, deep nesting and unrelated responsibilities. The file is 33 lines with one function that does one job, and the comment explains why the row is locked. All files are well under 500 lines.

**Testing receipts**

- Happy path: `test_admin_deletes_teacher_without_classes` confirms an admin gets a 204 and the delete query runs.
- Negative cases: `test_teacher_with_classes_is_not_deleted` confirms a 409 and that no delete runs. `test_unknown_teacher_returns_404` confirms a 404. `test_only_logged_in_admins_can_delete` confirms no session gives 401 and teacher or student sessions give 403. `test_database_failure_returns_503` confirms a 503.
- Integration: `test_delete_after_reassign_keeps_student_data` uses the real PostgreSQL database. It checks that a teacher with a class is refused (409), then reassigns the class, deletes the teacher (204), and confirms the student's enrollment still exists. It cleans up its test data and is skipped if `DATABASE_URL` is not set.
- The unit tests use a small fake database connection, so they run anywhere, including CI.
- Tests are in `tests/backend/test_teacher_deletion.py`.
- Regression: the full backend suite passed (182 tests). The only existing code file changed is `main.py` (2 lines added). Backend CI run: [CI Run](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/38954099092/job/117152488541)


## PR #83: Admin deletes student accounts (branch `40-admin-delete-student-accounts`, into `main`)

**Size:** 4 files changed, +166 / -0 lines (`src/backend/student_deletion.py` added, `tests/backend/test_student_deletion.py` added, `src/backend/main.py` updated with 2 lines, `README.md` updated with a new section).

- As part of the admin account management requirement (task #40), an admin must be able to remove a student account, for example when a student leaves the course or a test account needs cleaning up.
- Therefore, I implemented `DELETE /api/admin/students/{student_id}` in `src/backend/student_deletion.py`. It returns 204 on success. The student's enrollments, languages and sessions are removed together with the account by the database, and the classes themselves are kept.

**Review receipts**

- When I reviewed the endpoint, I noticed that a plain "delete this user id" query would also delete a teacher or an admin if someone passed their id. Therefore, the delete query only matches rows where `role = 'student'`. A teacher or admin id gets 404 "Student not found", so this route can only ever delete students.
- The check and the delete happen in one query (`DELETE ... RETURNING id`), so there is no gap between checking and deleting.
- Deleting the student's sessions with the account means a deleted student is logged out right away and their old session cookie stops working.
- The requirement says the student should "no longer appear in the account list". There is no account list endpoint yet, so the test checks that the user row is gone from the database instead.
- I reused `require_admin` and `database_unavailable` from `admin.py`. No existing lines were changed, and there is no temporary code.

**Architecture receipts**

- `student_deletion.py` is a new FastAPI router in `src/backend/`, matching the teacher deletion router, and the test is in `tests/backend/` as required. The only existing code file I touched is `main.py` (2 lines).
- In the DFD, this sits inside the backend admin process. After the admin check, the endpoint deletes one `users` row with role `student` in PostgreSQL. The existing foreign key cascades remove the matching rows in `students`, `class_enrollments`, the student's languages and `sessions`. The `classes` table is not touched.
- No new migration was needed.

**Clean Code Check**

- I re-read the file and tests for hardcoded values, duplicate code, dead code, deep nesting and unrelated responsibilities. The file is 27 lines with one function and one query, and the comment explains why the role is part of the query.

**Testing receipts**

- Happy path: `test_admin_deletes_student` confirms an admin gets a 204.
- Negative cases: `test_unknown_student_returns_404` confirms a 404. `test_only_logged_in_admins_can_delete` confirms no session gives 401 and teacher or student sessions give 403. `test_database_failure_returns_503` confirms a 503.
- Integration: `test_delete_student_against_database` uses the real PostgreSQL database. It checks that a teacher's id is refused (404), that the student and their enrollment are removed, and that the class still exists. It cleans up its test data and is skipped if `DATABASE_URL` is not set.
- Tests are in `tests/backend/test_student_deletion.py`.
- Regression: the full backend suite passed (181 tests). The only existing code file changed is `main.py` (2 lines added). Backend CI run: [CI Run](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/38958761562/job/117168191031)


## PR #84: Admin adds other admin accounts (branch `50-admin-admin-can-add-other-admin-accounts`, into `main`)

**Size:** 4 files changed, +203 / -0 lines (`src/backend/admin_creation.py` added, `tests/backend/test_admin_creation.py` added, `src/backend/main.py` updated with 2 lines, `README.md` updated with a new section).

- As part of the admin account requirement (task #50), an existing admin must be able to create more admins. The seed script from #52 only creates the very first admin, and our client will be an admin at handover who won't use the database or server directly, so she needs a way to add new admins through the app.
- Therefore, I implemented `POST /api/admin/admins` in `src/backend/admin_creation.py`. It takes `email`, `username`, `password`, `first_name` and `last_name`, and returns 201 with `id`, `email`, `username` and `role: "admin"`. The new admin can then log in with that email and password.

**Review receipts**

- This endpoint is only usable by someone already logged in as an admin (401 if not logged in, 403 for teachers and students). This is the logged-in-only endpoint I planned in #52, where I chose not to make a public "create admin" endpoint.
- Instead of writing new validation, the `NewAdmin` model reuses `TeacherSignup` from teacher signup (#45). This gives the same rules (valid email, password between 8 characters and 72 bytes, no blank username) and also blocks extra fields like `"role"`, so the rules stay in one place.
- The password is stored with our existing `hash_password` (#43), never as plain text. A duplicate email or username gives 409 "Email or username already in use", and database errors give 503 without exposing internal details.
- `/docs` shows an example request body, so the client or the frontend team can try it without reading the code.
- I reused `require_admin` and `database_unavailable` from `admin.py`. No existing lines were changed.

**Architecture receipts**

- `admin_creation.py` is a new FastAPI router in `src/backend/`, the same style as the other admin routers, and the test is in `tests/backend/` as required. The only existing code file I touched is `main.py` (2 lines).
- In the DFD, this sits inside the backend admin process. After the admin check, the new admin's details are validated, the password goes through `hash_password`, and one `users` row with role `admin` is written to PostgreSQL. The new admin then goes through the existing login process (#44).
- Together with the seed script (#52), this completes the admin account flow: the first admin comes from the script, and every admin after that is created through this endpoint.
- No new migration was needed.

**Clean Code Check**

- I re-read the file and tests for hardcoded values, duplicate code, dead code, deep nesting and unrelated responsibilities. The file is 42 lines with one model and one function. The only hardcoded value is the role `'admin'`, which is the purpose of this endpoint.

**Testing receipts**

- Happy path: `test_admin_creates_admin_with_hashed_password` confirms an admin gets a 201 with the right fields, the email is trimmed and lowercased, and the saved password is a bcrypt hash that matches the original but is not the plain text.
- Negative cases: `test_duplicate_email_or_username_returns_409` confirms a 409. `test_invalid_details_return_422` covers 5 cases (bad email, short password, password over 72 bytes, blank username, extra `role` field) and confirms nothing is inserted. `test_only_logged_in_admins_can_create_admins` confirms no session gives 401 and teacher or student sessions give 403. `test_database_failure_returns_503` confirms a 503.
- Integration: `test_new_admin_can_log_in` uses the real PostgreSQL database. A seeded admin creates a new admin (201), creating the same email again gives 409, and the new admin logs in through `POST /api/auth/login` and gets the `admin` role. It cleans up its test data and is skipped if `DATABASE_URL` is not set.
- Tests are in `tests/backend/test_admin_creation.py` (12 new tests).
- Regression: the full backend suite passed (186 tests). The only existing code file changed is `main.py` (2 lines added). Backend CI run: [CI Run](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/38961221247/job/117176471313)


## PR #85: Admin adds students to classes (branch `75-admin-admin-can-add-students-to-classes`, into `main`)

**Size:** 4 files changed, +231 / -0 lines (`src/backend/admin_enrollment.py` added, `tests/backend/test_admin_enrollment.py` added, `src/backend/main.py` updated with 2 lines, `README.md` updated with a new section).

- As part of the admin class management requirement (task #75), an admin must be able to enroll a registered student in any class, for example when a teacher is away or a student was missed.
- Therefore, I implemented `POST /api/admin/classes/{class_id}/students` in `src/backend/admin_enrollment.py`. It takes `{"student_number": "..."}` and returns 201 with `class_id`, `student_id` and `student_number`. Unlike the teacher version, it works on any class, not just ones the caller teaches.

**Review receipts**

- I kept the request, response and error messages the same as Ashish's teacher enrollment endpoint (#78), so the frontend can treat both endpoints the same way. I did not edit his code.
- The class is checked before the student, so a bad class gives 404 "Class not found" and an unknown student number gives 404 "Student not found". In both cases nothing is inserted.
- A student who is already in the class gives 409 "Student already enrolled". This comes from the database's unique rule on enrollments, so even two requests at the same moment can't create a duplicate.
- The student number is trimmed and limited to 30 characters, extra fields are blocked, and a class id that isn't a valid id gives 422.
- I reused `require_admin` and `database_unavailable` from `admin.py` and `RequiredText` from `schemas.py`. No existing lines were changed. Assigning a teacher to a class was already covered by #49, so this PR only handles students.

**Architecture receipts**

- `admin_enrollment.py` is a new FastAPI router in `src/backend/`, the same style as the other admin routers, and the test is in `tests/backend/` as required. The only existing code file I touched is `main.py` (2 lines).
- In the DFD, this sits inside the backend admin process. After the admin check, the endpoint reads `classes` and `students`, then writes one row to `class_enrollments` in PostgreSQL.
- It writes to the same `class_enrollments` table as the teacher endpoints (#78, #80), so a student added by an admin shows up for the teacher and can be removed by them as normal. No new migration was needed.

**Clean Code Check**

- I re-read the file and tests for hardcoded values, duplicate code, dead code, deep nesting and unrelated responsibilities. The file is 43 lines with one model and one function, and the checks run in a flat order with no deep nesting.
- One thing I noticed across all four of my PRs this week: each endpoint repeats the same "open a connection, and turn database errors into a 503" block. It is only a few lines each time and keeps every file easy to read on its own, but it could be pulled into one shared helper in a later refactor PR.

**Testing receipts**

- Happy path: `test_admin_enrolls_student_in_any_class` confirms an admin gets a 201 with the right fields, the enrollment row is inserted, and spaces around the student number are trimmed.
- Negative cases: `test_unknown_class_returns_404` and `test_unknown_student_returns_404` confirm a 404 and that nothing is inserted. `test_already_enrolled_returns_409` confirms a 409. `test_invalid_details_return_422` covers blank, too long, missing and extra-field cases, and `test_invalid_class_id_returns_422` covers a bad class id. `test_only_logged_in_admins_can_enroll` confirms 401 and 403. `test_database_failure_returns_503` confirms a 503.
- Integration: `test_admin_enrolls_student_in_another_teachers_class` uses the real PostgreSQL database. It sets up an admin, a teacher, a class and a student, enrolls the student into the teacher's class (201), tries again (409), and confirms there is exactly one enrollment row. It cleans up its test data and is skipped if `DATABASE_URL` is not set.
- Tests are in `tests/backend/test_admin_enrollment.py` (14 new tests).
- Regression: the full backend suite passed (188 tests). The only existing code file changed is `main.py` (2 lines added). Backend CI run: [CI Run](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/38962703614/job/117181482466)

## Code reviews for teammates
Some of the reviews from this week:

**PR #77: Merge dev to main (Ashish)**

- I approved the merge of `dev` into `main`. From this week, all of our PRs target `main` directly per TA feedback, which is why my four PRs above go into `main`. The large size of this PR was expected, since it brought in all of our earlier merged work, so the PR size limits don't really apply to it.

**PR #76: Teachers can create classrooms (Ashish)**

- I reviewed `POST /api/teacher/classes`. Ashish added a `require_teacher()` check that works like `require_admin()`. He pointed out that the remaining duplicated login-check code is better fixed in its own refactor PR, since it means updating tests, and I agreed.
- I also noted two features for later PRs, not this one: admins creating classes (an admin would need to pick which teacher owns the class, so it fits best in the admin code), and students joining with an invite code (the `class_code` this PR already makes would work well for that).

**PR #78: Teachers add students to classes (Ashish)**

- I liked that the class is checked before the student, so teachers can't use the endpoint to find out which student numbers exist, and that a test sends an extra `"role": "admin"` field to make sure it's blocked.
- The main issue I flagged was that the test file imports fixtures from `test_teacher_access.py`. If that file changes, these tests could break too. I suggested moving shared fixtures into a `conftest.py` in a later refactor PR. It is not a blocker.

**PR #80: Teachers remove a student from a class (Ashish)**

- I liked that the test confirms the student's account still exists after they are removed from the class, and his note about clearing class-specific data (like progress) later.
- The main thing to watch was merge order: this PR builds on #71 and #73, so those have to be merged first.


