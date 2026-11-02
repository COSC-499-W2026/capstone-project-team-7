### Week 8 — Madiba Burks Magara

October 26–November 1, 2026

Merged this week: [PR #184 — Teacher Dashboard Demo](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/184), [PR #186 — Create classes demo](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/186), and [PR #188 — Teacher demo: manage class rosters](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/188), all into `main`. Together, these let a teacher log in, see their classes and join codes, create a class, and manage its enrolled students.

Only merged PRs are included in this log. Merge status, review feedback and change sizes were checked against GitHub while writing it. Dates use Vancouver time: all three merges occurred on November 1 locally, although GitHub's UTC timestamps show November 2. Test counts below are recorded development runs from the relevant snapshots, not new executions for this documentation. Browser checks and screenshots used sample data rather than a deployed database.

---

### For PR #184 — Teacher Dashboard Demo

- [x] For [issue #183](https://github.com/COSC-499-W2026/capstone-project-team-7/issues/183), I replaced the teacher's placeholder "Logged in" screen with `TeacherDashboard.tsx`. I kept the existing demo's layout, fonts and plain controls rather than adding a separate visual design.
- [x] The dashboard uses the existing `GET /api/teacher/classes` endpoint to list the signed-in teacher's assigned classes. It selects the first available class, allows switching classes, and shows the selected class's language and join code.
- [x] I handled loading, teachers with no assigned classes, permission/server/network failures, retry and logout. Expired sessions return to login, and the class-loading effect ignores results after the dashboard unmounts.
- [x] Ashish requested that the dashboard stop hardcoding language names. Gamu pointed to the shared `utils/languageName.ts` helper from [#182](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/182). I used that helper to format codes returned by the class API and removed the dashboard's fixed language map.
- [x] I checked that a class with the code `it` displays as Italian without adding another dashboard mapping, and that an unknown code falls back to the code itself. This uses `Intl.DisplayNames`; it does not introduce a new database-backed language-list endpoint.
- [x] Reviewers also requested frontend screenshots. I added populated and empty dashboard screenshots under `docs/screenshots/`, linked them from the README, and included them in the PR description. The screenshots use sample classes.
- [x] I added React/React DOM deduplication to the Vitest configuration so component tests outside the frontend directory use the same React instance. The feature added no dependencies, backend endpoints or schema changes.
- [x] Ashish, Gamu and Dan reviewed the dashboard. Ashish confirmed that teacher login showed the teacher's classes and join codes, and approved after the shared-helper change. GitHub reports 136 additions and 2 deletions across the final PR.
- [x] In the DFD, this connects the teacher actor to the class-access API and PostgreSQL class records. The existing backend remains responsible for session, role and class-ownership checks.

For Tests:

- [x] [`tests/frontend/teacherDemo.test.ts`](https://github.com/COSC-499-W2026/capstone-project-team-7/blob/a200629/tests/frontend/teacherDemo.test.ts) covers populated and empty class responses, the request path, expired sessions, permission/server errors, network failure messaging and the initial loading screen.
- [x] [`tests/frontend/languageName.test.ts`](https://github.com/COSC-499-W2026/capstone-project-team-7/blob/a200629/tests/frontend/languageName.test.ts) checks French, Italian and unknown-code fallback.
- [x] The initial dashboard run passed **69 frontend tests**. After the language-helper review changes, `cd src/frontend && npm test` passed **72 tests**, and `npm run build` passed.
- [x] Browser checks verified class switching, language/join-code display, loading and empty states, failed loading and retry, expired sessions, logout failure/recovery and mobile layout. Additional checks verified Italian and unknown language codes using controlled API responses.

---

### For PR #186 — Create classes demo

- [x] For [issue #185](https://github.com/COSC-499-W2026/capstone-project-team-7/issues/185), I added `CreateClassForm.tsx` to the teacher dashboard. Teachers enter a class name, choose a supported language and submit to the existing `POST /api/teacher/classes` endpoint.
- [x] I trimmed the class name and rejected blank or whitespace-only submissions. The form disables controls while saving and uses an in-flight guard so repeated submission events do not create duplicate classes.
- [x] A successful request adds the returned class to the dashboard and selects it immediately, showing its language and server-generated join code. Failed requests preserve the entered name and language so the teacher can correct or retry the submission.
- [x] I shared session, permission and network handling between class loading and creation through `classResponse` in `api/teacher.ts`. Validation errors receive an actionable message, expired sessions return to login, and a response arriving after the form unmounts does not update the dashboard.
- [x] I updated the branch after the dashboard merged and resolved the overlapping dashboard, test and README changes. I restored the teacher-class API documentation after a conflict resolution had replaced that section with a stray character.
- [x] In response to Gamu's review, I moved `languages.ts` into `utils/`, beside `languageName.ts`, updated the form import and removed an unused dashboard import. The dashboard uses the shared name formatter; the creation form still offers the six supported language choices. Adding a new creation choice remains separate work.
- [x] Ashish and Gamu confirmed that class creation worked and requested screenshots. I added screenshots of the filled New class form and the newly selected class, then updated the README and PR description. GitHub reports 135 additions and 5 deletions in the final comparison with `main`.
- [x] In the DFD, the teacher's class details pass from the form to the authenticated class-creation API, which writes the teacher-owned class to PostgreSQL and returns its join code. I reused that backend flow without a migration or new dependency.

For Tests:

- [x] [`tests/frontend/createClass.test.ts`](https://github.com/COSC-499-W2026/capstone-project-team-7/blob/5c7162f/tests/frontend/createClass.test.ts) checks the POST body, trimmed name, returned class/join code, expired sessions, permission/validation/server/network failures, six language options and disabled controls.
- [x] The initial creation snapshot passed **77 frontend tests** and the production build. After updating from `main` and addressing review, the frontend suite passed **110 tests**, and the build passed again. These totals include other frontend features merged between the two snapshots.
- [x] Browser checks covered whitespace rejection, duplicate-submission prevention, pending controls, automatic selection and join-code display, creating the first class for a teacher, and error recovery without losing the entered fields.
- [x] I also checked expired sessions, mobile layout and logout while creation was pending. Releasing the delayed response afterward left the login page intact. These checks used a local sample-data API, not a claim of deployed end-to-end verification.

---

### For PR #188 — Teacher demo: manage class rosters

- [x] For [issue #187](https://github.com/COSC-499-W2026/capstone-project-team-7/issues/187), I added `ClassRoster.tsx` to the selected teacher class. It lists enrolled students' names and student numbers using the existing roster endpoint, with loading, empty and error states.
- [x] Teachers can add an already registered student by student number or remove their enrollment. Student numbers remain strings, preserving leading zeroes. The roster reloads after successful changes; removing enrollment keeps the student account available for re-enrollment.
- [x] I extended the shared teacher API module with roster GET, POST and DELETE requests. It handles missing classes/students, duplicate enrollment, invalid input, permission failures, unavailable services and expired sessions without exposing internal errors.
- [x] I guarded mutation requests against repeated clicks and ignored results after a class view unmounts. Switching classes resets the roster, so a delayed response from the previous class cannot replace the currently selected class's students.
- [x] I merged the reviewed class-creation work from `main`, resolved the overlaps and kept the shared language helper and creation form. The resulting PR comparison contains roster changes rather than repeating the earlier dashboard features.
- [x] Gamu requested confirmation before removal because one misclick could otherwise remove enrollment. I added `window.confirm` naming the student and explaining that their account is kept. Cancelling sends no DELETE request.
- [x] Gamu also noted that failed additions showed "Reload students" even though the roster had loaded successfully. I limited that button to roster-loading failures. Failed add/remove requests keep the loaded list and show the error without suggesting an unnecessary reload.
- [x] Dan and Gamu approved the roster work. I added populated and empty roster screenshots and documented the controls in the README and PR description. The final text diff has 172 additions and 3 deletions, plus two PNG screenshots. No backend, database, dependency or styling changes were needed.
- [x] In the DFD, the teacher selects an owned class, reads its enrollments, and sends enrollment changes through the protected class API. PostgreSQL stores the enrollment changes; deleting a student account is not part of this flow.

For Tests:

- [x] [`tests/frontend/manageRoster.test.ts`](https://github.com/COSC-499-W2026/capstone-project-team-7/blob/07a316e/tests/frontend/manageRoster.test.ts) covers roster requests, successful responses, empty results, trimmed student numbers, session/permission failures, missing students, duplicate enrollment, invalid input, server/network errors and the initial loading controls.
- [x] The updated branch passed **122 frontend tests** with `cd src/frontend && npm test`; `npm run build` also passed. The same checks passed after the confirmation/reload review fixes.
- [x] Browser checks exercised viewing, adding, removing and re-adding students; duplicate and missing-student errors; retry; leading-zero numbers; class switching; expired sessions; logout; mobile layout; and the existing class-creation and student/admin routes.
- [x] Review regression checks verified both cancellation and confirmation: cancellation sent no DELETE and kept enrollment; confirmation sent one DELETE and updated the roster. Failed add/remove requests retained the list without a reload button, while a failed roster load showed the button and retried successfully.
- [x] These interaction checks used sample data and controlled browser responses, including simulated confirmation choices. They do not establish a separate real-database or physical-phone test run.

---

## How this fits the overall system

This work extends the teacher side of the same minimal demo as the student dashboard. Teachers can now move from login to their own classes, create a class and share its join code, then view and manage registered students in its roster. The frontend reuses the team's cookie-session authentication and existing class APIs, while the backend continues to enforce teacher roles and ownership.

I responded to review by reusing Ashish's language-name helper, grouping language utilities together, adding screenshots and making enrollment removal safer. I also reviewed and approved Dan's [difficulty-based scoring in #178](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/178). My approval is a review contribution, not evidence that I independently reran his backend tests.

Next steps are to test the combined teacher/student journey with real accounts and PostgreSQL, including sharing a newly created class code, student enrollment and teacher roster updates. Teacher-assigned hunts, student progress reporting and a database-backed language-choice list remain separate work. No application tests were rerun while writing this documentation.
