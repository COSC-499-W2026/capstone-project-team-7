### Week 6: Ashish Nayak
Oct 12 to Oct 18

**Contents**

1. [Summary](#1-summary)
2. [PR #76: Teachers create classes](#2-pr-76-teachers-create-classes)
3. [PR #78: Teachers add students to classes](#3-pr-78-teachers-add-students-to-classes)
4. [PR #80: Teachers remove students from classes](#4-pr-80-teachers-remove-students-from-classes)
5. [PR #89: Students join a class with its code](#5-pr-89-students-join-a-class-with-its-code)
6. [Non Code PRs](#6-non-code-prs)
7. [Reviews I gave](#7-reviews-i-gave)
8. [How this fits the overall system](#8-how-this-fits-the-overall-system)

---

## 1. Summary

Merged this week: 4 code PRs on `main` (#76, #78, #80, #89) and 1 process PR on `main` (#82).

| PR | Issue | Requirement | Size | Reviewers |
|---|---|---|---|---|
| #76 Create class | #73 | Teachers can create classes | 3 files, +98/−5 | Gamu, Dan |
| #78 Add student to class | #71 | Teachers can add students to specific language classes | 5 files, +164/−4 | Gamu, Dan |
| #80 Remove student from class | #74 | Teachers can remove a student from their class | 3 files, +89/−2 | Gamu, Dan |
| #89 Join class with code | #79 | Students can self-enrol into classes using the class code | 4 files, +201 | Gamu, Dan |

PRs 76, 78, 80 and 89 are my merged code PRs this week. They build on each other: #78 uses the `require_teacher` check from #76, #80 adds to the classes module created in #78, and #89 writes to the same enrollment table from the student side. I merged them in that order.

**Claim labels.** *Observed* means I ran it or saw it (test output, review text). *Generated* means AI-written code that I reviewed. "Re-run" test counts come from running `python -m pytest tests/backend` at each merge commit on Oct 17 against my local PostgreSQL, with `TEST_DATABASE_URL` set so no integration tests were skipped. All four PRs were approved by Gamu and Dan, and the CI backend and frontend jobs passed on the final commit of each (observed on GitHub).

---

## 2. PR #76: Teachers create classes

Endpoint: `POST /api/teacher/classes`

- [x] As part of the requirement "the system shall allow teachers to create classes" (#73), a logged-in teacher needs to give a class a name and a language and get back a class they own, with a class code students can use later. Therefore, I implemented create_class() in teacher_access.py, along with a require_teacher() check. The teacher is always taken from the session, never from the request body, so a teacher can only create classes for themselves. Students and admins get 403, which covers the requirement's negative case.
- [x] When I reviewed the generated create_class(), I noticed it turned every foreign key error into "Unknown language" (422). The classes table has two foreign keys (language_code and teacher_id), so a teacher account with no teachers row would have been wrongly blamed on the language. Therefore, I narrowed the 422 to the classes_language_code_fkey constraint only, and any other failure returns 503.
- [x] When reviewing the request model, I found that language codes longer than 5 characters would reach Postgres and fail as "value too long", coming back as a misleading 503. Therefore, I added max_length=5 to match languages.code, so it is a 422 before the database is touched.
- [x] The PR does not contain any temporary workaround because classes, language codes and class codes already exist in migration 001. The class code comes from the database default, so no new code generates it.
- [x] The PR contains small functions: require_teacher (4 lines), create_class (about 15 lines) and database_unavailable (3 lines).
- [x] I reused current_user from auth.py and RequiredText from schemas.py, and moved the repeated 503 into one database_unavailable() helper. I can confirm the contribution does not contain any of the following:
  - hardcoded values
  - duplicate code within my change
  - dead code
  - unnecessary function calls
  - excessive conditional logic
  - deep nesting
  - high cyclomatic complexity
  - classes/modules/functions with many unrelated responsibilities

  Limitation: the existing GET class routes (Dan's #56) still used their own session SQL (teacher_connection). I mentioned this in the PR conversation and left the refactor out of this PR to keep it small. Dan is working with #95 to move them onto current_user.
- [x] Gamu and Dan approved. Gamu suggested two follow-ups for later PRs: admins creating classes and students joining with the class code. The second became my PR #89.
- [x] This work is written in teacher_access.py because that module already owns "classes owned by the signed-in teacher", and create is the same feature area.
- [x] This work belongs in 9.2 Create / Delete Class of the Class Management DFD (Level 2). It writes class data to D1 User Data SQL, which feeds the class list in 9.1 View All Classes.

**Data receipts**

- [x] Class input is validated by the Pydantic model ClassCreate: the name is trimmed and must not be blank, language_code is at most 5 characters, and extra fields are rejected (so teacher_id or class_code can't be sent). An unknown language is caught by the real foreign key and returned as 422. I chose this over a separate SELECT from languages because it is one query and leaves no gap between check and insert.
- [x] Access control: only the teacher role can write classes, and the owner always comes from the session. As a second layer, classes.teacher_id references teachers(user_id), so the database itself rejects a class owned by a non-teacher.

**Tests (same PR)**

- [x] Happy path: `test_teacher_creates_class` passed. It checks the 201 body, the trimmed name ("  French 101  " saved as "French 101"), the 12 character class code, and that the new class shows up in `GET /api/teacher/classes`, proving it was saved.
- [x] Abnormal: these returned **503** `{"detail": "Database unavailable"}` with no internal details:
  - `test_create_class_database_failure_is_safe` (fails during the session check)
  - `test_create_class_insert_failure_is_safe` (login works, the insert fails)
- [x] Negative: these failed as expected:
  - `test_create_class_rejects_bad_input` (5 cases: blank name, missing name, missing language, unknown language "xx", over-long language), all **422** with the class count unchanged
  - `test_create_class_requires_teacher` (no session **401**, student **403**, admin **403**), with `SELECT count(*) FROM classes` unchanged. The count check is what proves "the database does not create a new entry".
- [x] Unit: `test_create_class_database_failure_is_safe`. Integration (temporary Postgres schema, real login): every other test above. Integration is needed because the unknown-language case depends on the real foreign key.
- [x] Directory: `tests/backend/test_teacher_access.py`.
- [x] This PR did not break anything else in the system: CI passed, and a re-run at merge commit `a45165e` gives **185 passed**.

---

## 3. PR #78: Teachers add students to classes

Endpoint: `POST /api/teacher/classes/{class_id}/students`

- [x] As part of the requirement "the system shall allow teachers to add students to specific language classes" (#71), a teacher viewing one of their classes needs to add a registered student and be stopped if that student is already in the class. Therefore, I implemented enroll_student() in a new class_enrollment.py. The teacher sends a student number and gets back 201 with the class id, student id and student number. A student who is already enrolled gets 409 "Student already enrolled", which is the requirement's negative case.
- [x] When I reviewed the order of checks, I made the class check run before the student lookup. Otherwise a teacher could send any class id and use the 404 "Student not found" to test which student numbers exist.
- [x] The PR does not contain any temporary workaround because it writes to the class_enrollments table from migration 001. Its primary key (class_id, student_id) is what blocks duplicates, so no extra code is needed for the 409.
- [x] The PR contains small functions: enroll_student (about 20 lines) and owned_class (5 lines).
- [x] I reused require_teacher and database_unavailable from #76 and RequiredText from schemas.py, and pulled out owned_class as described above. I can confirm the contribution does not contain any of the following:
  - hardcoded values
  - duplicate code
  - dead code
  - unnecessary function calls
  - excessive conditional logic
  - deep nesting
  - high cyclomatic complexity
  - classes/modules/functions with many unrelated responsibilities
- [x] Gamu and Dan approved.
- [x] This work is written in a new class_enrollment.py because enrollment is its own feature area (one module per feature area), and teacher_access.py would otherwise keep growing with every class feature.
- [x] This work belongs in 9.6 Add / Delete Students of the Class Management DFD (Level 2). It writes the student roster to D1 User Data SQL.

**Data receipts**

- [x] An enrollment is modeled as a row in class_enrollments with a composite primary key (class_id, student_id). I relied on that key instead of checking first with a SELECT, so two requests at the same time still can't create two rows.
- [x] Student input is validated by EnrollmentRequest: the student number is trimmed, not blank, at most 30 characters (matching students.student_number), and extra fields are rejected.
- [x] Privacy: a class that doesn't exist and a class owned by another teacher return the same 404 "Class not found", so a teacher can't discover other teachers' classes.

**Tests (same PR)**

- [x] Happy path: `test_teacher_enrolls_student_in_owned_class` passed: 201, exact body, a padded " 12345678 " still matches, and exactly one class_enrollments row with the right ids.
- [x] Abnormal: `test_session_check_database_failure_is_safe` and `test_enrollment_database_failure_is_safe` returned **503** with no internal details.
- [x] Negative: these failed as expected:
  - `test_already_enrolled_student_is_rejected`: first add 201, second add **409**, still exactly one row (the requirement's negative case)
  - `test_missing_or_unowned_class_is_hidden`: **404** "Class not found", no rows
  - `test_unknown_student_number_is_not_found`: **404** "Student not found", no rows
  - `test_invalid_body_is_rejected`: missing, blank, 31 characters, a number, extra field, all **422** with no rows
  - `test_requires_teacher`: no session **401**, student and admin **403**, no rows
- [x] Unit: `test_session_check_database_failure_is_safe`. Integration (temporary Postgres schema, real login): every other test above. Integration is needed because the 409 comes from the real primary key.
- [x] Directory: `tests/backend/test_class_enrollment.py`.
- [x] This PR did not break anything else in the system: CI passed, and a re-run at merge commit `8d391dd` gives **199 passed**, including the existing get_class tests after the owned_class refactor.

---

## 4. PR #80: Teachers remove students from classes

Endpoint: `DELETE /api/teacher/classes/{class_id}/students/{student_id}`

- [x] As part of the requirement "the system shall allow teachers to remove a student from their class" (#74), a teacher needs to take a student off one class roster without deleting the student's account. Therefore, I implemented remove_student() in class_enrollment.py. It returns 204, or 404 "Student not enrolled" if there was nothing to remove. Students and admins get 403, which is the requirement's negative case.
- [x] When I reviewed the generated remove_student(), I did not find a problem with the core logic. It is one DELETE scoped to (class_id, student_id), and rowcount tells it whether anything was removed, so there is no separate lookup and no gap between a check and the delete. I checked this by running the tests against Postgres and by asserting that the student's account and other enrollments survive.
- [x] The PR contains one temporary limitation, not a workaround. The requirement says the student's "class-specific data is cleared", but no class-specific progress tables exist yet (game sessions will be coming in a later week). I wrote this in the PR as a known limitation instead of adding placeholder code. When those tables are added, they should cascade from the enrollment.
- [x] The PR contains one function, remove_student(), of about 15 lines.
- [x] I reused require_teacher, owned_class and database_unavailable from #76 and #78, so the route adds no new session or ownership SQL. I can confirm the contribution does not contain any of the following:
  - hardcoded values
  - duplicate code
  - dead code
  - unnecessary function calls
  - excessive conditional logic
  - deep nesting
  - high cyclomatic complexity
  - classes/modules/functions with many unrelated responsibilities
- [x] This work is written in class_enrollment.py because removing is the undoing of enrolling and uses the same table and helpers.
- [x] This work belongs in 9.6 Add / Delete Students of the Class Management DFD (Level 2).

**Data receipts**

- [x] Access control: only the teacher who owns the class can remove from it. Another teacher's class returns the same 404 "Class not found" as a missing class, and students and admins get 403. Only the enrollment row is deleted: the users and students rows, other enrollments and studied languages are untouched.

**Tests (same PR)**

- [x] Happy path: `test_teacher_removes_enrolled_student` passed: 204, the enrollment row is gone, and the student's account and other data still exist.
- [x] Abnormal: `test_remove_database_failure_is_safe` returned **503** with no internal details.
- [x] Negative: these failed as expected:
  - `test_remove_requires_teacher`: no session **401**, student and admin **403**, enrollment still there (the requirement's negative case)
  - `test_removing_student_not_enrolled_is_not_found`: **404** "Student not enrolled"
  - `test_remove_from_missing_or_unowned_class_is_hidden`: **404** "Class not found", enrollment still there
  - `test_remove_with_invalid_ids_is_rejected`: a class id or student id that isn't a UUID, **422**
- [x] All are integration tests (temporary Postgres schema, real login) because the point is that exactly one row is deleted and nothing else is. A fake connection could not show that.
- [x] Directory: `tests/backend/test_class_enrollment.py`.
- [x] This PR did not break anything else in the system: CI passed, and a re-run at merge commit `03a1259` gives **235 passed**.

---

## 5. PR #89: Students join a class with its code

Endpoint: `POST /api/student/classes/join`

- [x] As part of the requirement "students should be able to self-enrol into classes using the class code" (#79), a logged-in student needs to type the code their teacher shared and end up in that class. This is a second way into a class alongside #78, where the teacher adds them. Therefore, I implemented join_class() in a new student_enrollment.py with a require_student() check. The student gets back 201 with the class id, name and language. A code that matches no class returns 404 "Class not found" and creates nothing, which is the requirement's negative case.
- [x] When I reviewed the generated JoinClassRequest, I checked that trimming and uppercasing the code is safe before keeping it. Generated codes are 12 uppercase hex characters (migration 001), so two classes can never differ only by case, and uppercasing can't match the wrong class. Students might type the code in lowercase on a phone, so " abc123def456 " still matches. Limitation: if teachers can ever choose their own codes, those must be stored uppercased too or we need to refactor this functionality. Currently the faeture stands as intended by the team.
- [x] When I reviewed the duplicate case, I noticed the teacher enrol route on #71's branch already handled "already enrolled" as a 409, but #71 wasn't merged into this branch yet. Rather than copy code from an unmerged branch, I merged #71 in first and then used the same pattern: the class_enrollments primary key raises UniqueViolation and the route returns 409 "Already enrolled".
- [x] The PR does not contain any temporary workaround because it reuses the class_code column and its database default from migration 001 and the class_enrollments table from #78. No migration was needed.
- [x] The PR contains small functions: require_student (4 lines) and join_class (about 18 lines).
- [x] I reused current_user from auth.py, RequiredText from schemas.py and database_unavailable from teacher_access.py. I can confirm the contribution does not contain any of the following:
  - hardcoded values
  - duplicate code
  - dead code
  - unnecessary function calls
  - excessive conditional logic
  - deep nesting
  - high cyclomatic complexity
  - classes/modules/functions with many unrelated responsibilities

  Limitation: there are now three role checks (require_admin, require_teacher, require_student) with different 403 messages. A single require_role() in auth.py would remove the repetition. This would be its own follow-up issue rather than part of this PR.
- [x] Gamu and Dan approved.
- [x] This work is written in a new student_enrollment.py instead of class_enrollment.py because class_enrollment.py is the teacher router (`/api/teacher/classes`, require_teacher). Putting a student route there would mix two roles and two URL prefixes in one module.
- [x] This work belongs in 9.6 Add / Delete Students in the Class Management DFD, because it writes to the same student roster in D1 User Data SQL. The DFD only shows the teacher entering this process, so the student path should be added to the diagram.

**Data receipts**

- [x] The class code is validated by JoinClassRequest: trimmed, not blank, at most 12 characters (matching classes.class_code), uppercased, and extra fields rejected.
- [x] Access control: only the student role can join, and the student id always comes from the session, so a student can only enrol themselves. Teachers and admins get 403.
- [x] The class code could be guessed to join a class without being invited. A code is 12 hex characters (48 bits), so brute force isn't practical, but the route has no rate limiting yet. I noted this as a follow-up if we decide to implement that.

**Tests (same PR)**

- [x] Happy path: `test_student_joins_class_with_code` passed for "ABC123DEF456" and "  abc123def456  ": 201, exact body, and one class_enrollments row for that student and class.
- [x] Abnormal: these returned **503** `{"detail": "Database unavailable"}` with no internal details:
  - `test_session_check_database_failure_is_safe` (fails in current_user)
  - `test_join_database_failure_is_safe` (fails in join_class)
- [x] Negative: these failed as expected:
  - `test_unknown_code_returns_not_found`: **404** "Class not found", no rows (the requirement's negative case)
  - `test_joining_twice_returns_conflict`: first join 201, second **409** "Already enrolled", still exactly one row
  - `test_join_rejects_bad_input`: missing, blank, 13 characters, a number, extra field, all **422** with no rows
  - `test_join_requires_student`: no session **401**, teacher and admin **403**, no rows
  - `test_expired_session_is_rejected`: **401**, no rows
- [x] Unit: the two 503 tests (no database). Integration (temporary Postgres schema, real login): every other test above. Integration is needed because the 409 comes from the real primary key.
- [x] Directory: `tests/backend/test_student_enrollment.py`.
- [x] This PR did not break anything else in the system: CI passed, and a re-run at merge commit `7084e6f` gives **250 passed**.

---

## 6. Non Code PRs:
PR #82: Updates the PR template and AGENTS.md now that PRs target main instead of dev. Process change, no code.

---

## 7. Reviews I gave

| PR | Author | What I found | Outcome |
|---|---|---|---|
| #81 Admin deletes teacher accounts | Gamu | No issues. Refusing to delete a teacher who still has classes prevents unsupervised classes. | Approved, merged |
| #83 Admin deletes student accounts | Gamu | No issues. Suggested the team consider splitting tests into a fast critical run and a full run, since the backend suite now takes about 2 minutes. | Approved, merged |
| #84 Admin creates admin accounts | Gamu | Reuses teacher signup's fields and validation; good edge-case tests | Approved, merged |
| #90 Revert direct push to main | Madiba | The change-password commit had been pushed straight to main without review; reverting it lets it go through a normal PR (#93) | Approved, merged |
| #93 Change password | Madiba | The `FOR SHARE` on login is needed so a login racing a password change can't keep an old-password session; I ran it locally | Approved, not merged yet |
| #95 Shared auth refactor | Dan | Removes the duplicated session SQL I flagged in week 5 (#56, #58) and in #76; tests pass locally | Approved, not merged yet |

## 8. How this fits the overall system

Create class, add student and remove student are the teacher half of class management (9.0 in the DFD), and join by code is the student half. A teacher can now create a class, fill its roster and correct it, or share the class code and let students join themselves. Every route checks the session through current_user and ownership through the shared owned_class(), so a teacher can never read or change another teacher's class.

Week 7's tasks will revolve around game sessions and the core hunt game logic now that the key account and class related backend is implemented.
