### Week 9 — Madiba Burks Magara

November 2–8, 2026

Merged this week: [PR #217 — Add student class leaderboard API with equipped icons](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/217), [PR #219 — Profile Icons Student Leaderboard](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/219), and [PR #221 — Add admin dashboard for teacher approvals and class reassignment](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/221), all into `main`. Together, these add class rankings with students' equipped icons and a dashboard for two existing admin operations.

Only PRs I authored and personally merged this week are included. GitHub confirms `KoesOremus` as both author and merger for all three PRs. Merge dates and final change sizes were checked against GitHub while writing this log. Dates use Vancouver time: all three merges occurred on November 8 locally, although #219 and #221 have November 9 UTC timestamps. Test counts below are recorded development runs from their respective snapshots, not new executions for this documentation. Frontend browser checks used sample API responses; the leaderboard SQL integration test used temporary PostgreSQL 17.

---

### For PR #217 — Add student class leaderboard API with equipped icons

- [x] For [issue #216](https://github.com/COSC-499-W2026/capstone-project-team-7/issues/216), I added `GET /api/student/classes/{class_id}/leaderboard` in `src/backend/student_leaderboard.py` and registered its router in `main.py`.
- [x] I reused the existing cookie-session authentication and student-role dependency. Only students enrolled in the requested class can read its rankings. Invalid class IDs, missing classes, denied access and database failures receive the corresponding API errors.
- [x] The endpoint returns each enrolled student's username, rank, total points and equipped profile icon ID. Students without qualifying games receive zero points, and students without an equipped icon receive `null`.
- [x] I calculated totals from stored, completed game sessions in the class's language. Unfinished games and games in other languages are excluded; the endpoint does not accept scores supplied by the frontend.
- [x] Games currently have no direct class link. I documented that totals include games completed before enrollment and that classes sharing a language use the same language-specific game totals for their members.
- [x] Equal totals share a competition rank, such as 1, 1, 3. Usernames provide a consistent display order within ties without changing those shared ranks.
- [x] I reused existing game points, enrollment records and equipped-icon storage. No migration or dependency was needed. I documented the response, scoring rules, errors and test command in the README.
- [x] I kept the API and screen in separate PRs to meet the 200-added-line limit. The final API PR contains 176 additions and no deletions across four files.
- [x] In the DFD, the student sends a class-ranking request through the protected Backend API. PostgreSQL supplies class membership, completed-game points and the equipped icon ID; the API returns the resulting rankings to the frontend.

For Tests:

- [x] [`tests/backend/test_student_leaderboard.py`](https://github.com/COSC-499-W2026/capstone-project-team-7/blob/0f863eb2516ebf92f8bb5a528dace0eb0d920491/tests/backend/test_student_leaderboard.py) covers missing/invalid sessions, non-student roles, invalid UUIDs, missing classes, unenrolled students and safe database-failure responses.
- [x] The PostgreSQL integration case creates enrolled students and an outsider, then checks completed-game aggregation, excluded unfinished and other-language games, outsider exclusion, tied ranks, zero points and equipped/null icons.
- [x] The integration case also verifies actual class-access restrictions and rejection after the login session expires.
- [x] The focused leaderboard run passed **10 tests**. The full backend suite passed **713 tests** against temporary PostgreSQL 17, and `git diff --check` passed.

---

### For PR #219 — Profile Icons Student Leaderboard

- [x] For [issue #218](https://github.com/COSC-499-W2026/capstone-project-team-7/issues/218), I enabled the student dashboard's Leaderboard button and added `LeaderboardPage.tsx`. Students can choose an enrolled class, view its rankings and return to the dashboard.
- [x] I added `api/leaderboard.ts` to call the new backend endpoint. It handles network/server failures with friendly messages and uses the existing session-expiry error so the app can return to login.
- [x] I separated the ranking table into `LeaderboardTable.tsx`. It displays rank, username, points and the student's equipped artwork by reusing `ProfileIcon`; students without an equipped icon show a neutral circle.
- [x] The screen loads enrolled classes through the existing profile API. It shows loading feedback, a prompt for students who have no classes, and an empty-results message when there are no entries to display.
- [x] Failed requests offer Retry. If loading another class fails, the previous successful table remains visible with its original class caption, so its results are not presented as belonging to the failed selection.
- [x] I disabled class selection during loading and ignored responses after the screen unmounts. I added table spacing and responsive selection controls while keeping the existing application style.
- [x] During integration with `main`, I preserved both store and leaderboard navigation and retained both API and screen documentation in the README.
- [x] Ashish found a stray `main` token after the `StudentDashboard` function's opening brace, introduced during conflict resolution. I removed it in commit `02636c9`, reran the frontend tests and production build, and pushed the fix to the PR.
- [x] The initial implementation had 166 additions and 3 deletions. After integrating `main` and the review fix, GitHub reports a final comparison of 175 additions and 5 deletions across eight files, still below 200 added lines. No dependency or database changes were needed.
- [x] In the DFD, the student dashboard reads class membership from the profile API and requests rankings from the leaderboard API. The frontend renders the returned scores and icon IDs; it does not calculate or submit leaderboard scores.

For Tests:

- [x] [`tests/frontend/leaderboard.test.ts`](https://github.com/COSC-499-W2026/capstone-project-team-7/blob/02636c973de9deb0078b46823215d135e5401a27/tests/frontend/leaderboard.test.ts) covers successful and empty API responses, HTTP failures, expired sessions, network retry, initial loading, table captions, shared ranks, zero scores, equipped artwork and neutral fallbacks.
- [x] The initial screen snapshot passed **145 frontend tests** and `npm run build`. After the merge-conflict typo was corrected, the branch passed **165 frontend tests**, the TypeScript check and the production build. These totals come from different development snapshots.
- [x] Browser checks covered navigation, class selection, equipped icons, shared ranks, no enrolled classes, profile-loading retry and expired sessions. Repeated class-loading failures retained the previous table and caption; retrying after recovery loaded the selected class.
- [x] I checked the screen at a 375-pixel mobile viewport for horizontal overflow and captured a preview with sample students. These browser checks used controlled API responses, not a deployed or real-database end-to-end run.

---

### For PR #221 — Add admin dashboard for teacher approvals and class reassignment

- [x] For [issue #220](https://github.com/COSC-499-W2026/capstone-project-team-7/issues/220), I replaced the admin placeholder with `AdminDashboard.tsx`. `App.tsx` displays it for authenticated admin accounts while preserving student and teacher routing.
- [x] I added a teacher-signup approval form using the existing `POST /api/admin/approved-teachers` endpoint. The form explains that approval permits signup; it does not create the teacher's account.
- [x] I added a class-reassignment form using the existing `PATCH /api/admin/classes/{class_id}/teacher` endpoint. Admins enter the class UUID and a registered, approved teacher's email. Reassignment preserves enrollments and progress.
- [x] I added `api/admin.ts` to normalize email input, trim/encode the class ID, and translate permission, missing-class, duplicate-approval, invalid-input, network and service failures into friendly messages. Backend role checks remain responsible for authorization.
- [x] Successful submissions reset the relevant form and show confirmation. Failed submissions preserve the entered values so the admin can correct them or retry. A request guard prevents duplicate submissions, and both forms and logout are disabled while a request is pending.
- [x] Expired sessions return to login. Logout failures leave the dashboard available for retry, and late responses are ignored after the dashboard unmounts.
- [x] I documented the dashboard in the README and kept its scope to approval, reassignment and logout. Account lists and account creation/editing/deletion remain separate work. No backend, schema, dependency or styling changes were needed.
- [x] I merged the newer `main` changes without conflicts, reran the frontend checks, and committed and pushed the branch before opening the PR. The final comparison contains 162 additions and 1 deletion across five files.
- [x] In the DFD, the admin dashboard sends approval and class-ownership changes through existing protected admin endpoints. PostgreSQL stores the approved email or replacement teacher assignment; the frontend reports the result.

For Tests:

- [x] [`tests/frontend/adminDashboard.test.ts`](https://github.com/COSC-499-W2026/capstone-project-team-7/blob/135a1a3d40f4b2d13c745b1f89d27977a2afffd4/tests/frontend/adminDashboard.test.ts) covers request methods/bodies, input normalization, successful mutations, HTTP errors, session expiry, network retry and the initial labelled forms and logout control.
- [x] The initial implementation passed **166 frontend tests** and the production build. After merging the newer `main`, the branch passed **175 frontend tests**, `npm run build` and the PR diff's whitespace check.
- [x] Browser checks covered admin/student/teacher routing, required-field validation, successful approval and reassignment, duplicate approval, an invalid teacher, network failure/retry and preserved inputs after failure.
- [x] I verified that rapid duplicate submissions sent one request, pending controls were disabled, logout failure could be retried, expired sessions returned to login, and the mobile layout had no horizontal overflow. These interaction checks used sample API responses rather than real admin mutations against PostgreSQL.

---

## How this fits the overall system

The leaderboard connects the existing game-scoring and profile-icon features to the student dashboard. Students can now compare completed-game totals with classmates and see their equipped icons beside their names. Splitting the backend and frontend work kept each PR below the 200-added-line limit while allowing the API's access and scoring rules to be tested separately from rendering and request recovery.

The admin dashboard exposes two existing account/class-management operations through the frontend. Admins can approve teacher signup and transfer a class without changing its enrollments or game progress. This extends the teacher dashboard work from Week 8 while keeping permissions enforced by the backend.

Next steps are to verify the combined leaderboard and admin journeys with real accounts and PostgreSQL, clarify future class-specific scoring if games gain a class link, and scope the remaining account-management screens separately. The global leaderboard toggle remains separate work. No application tests were rerun while writing this documentation.
