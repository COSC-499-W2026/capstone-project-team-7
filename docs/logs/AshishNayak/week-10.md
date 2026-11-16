### Week 10: Ashish Nayak
Nov 9 to Nov 15

**Contents**

1. [Summary](#1-summary)
2. [PR #232: Shared frontend fetch helper](#2-pr-232-shared-frontend-fetch-helper)
3. [PR #228: Teacher clue audio form](#3-pr-228-teacher-clue-audio-form)
4. [PR #230: One shared role check](#4-pr-230-one-shared-role-check)
5. [PR #233: Keep enrollments when a student is removed](#5-pr-233-keep-enrollments-when-a-student-is-removed)
6. [Deploying the app for the demo](#6-deploying-the-app-for-the-demo)
7. [Reviews I gave](#7-reviews-i-gave)
8. [How this fits the overall system](#8-how-this-fits-the-overall-system)

---

## 1. Summary

**This was a bonus week.** It was reading week, so as a team we agreed that there would be no assigned sprint tasks. Whoever had time would work through the refactor plan from Nov 6 and anything else that moves us towards the Milestone 1 demo. I did three rows of that plan (the shared fetch helper, one shared role check, and the unknown-role crash), finished the teacher audio form I started in week 9, and did the backend half of #113 (keep a student's class data when they're removed). I also spent time working out how to deploy the app, and got the full system running on my own domain from my home laptop through a Cloudflare Tunnel.

| PR | Issue | Requirement | Size | Reviewers | Status |
|---|---|---|---|---|---|
| #232 Shared fetch helper | #231 | Logged-out and offline students are handled the same on every page | 8 files, +104/−28 | `<reviewers>` | Merged |
| #228 Clue audio form | #201 | Teachers can see their class's locations and upload clue audio | 6 files, +177/−1 | `<reviewers>` | Merged |
| #230 Shared role check | #229 | Every protected route checks the role the same way | 7 files, +102/−27 | `<reviewers>` | Merged |
| #233 Soft unenroll | #113 (part 1) | Teachers can still see a removed student's past data | 18 files, +141/−34 | `<reviewers>` | Merged |
| Roster shows removed students | #113 (part 2) | Teachers see who was removed and when | 7 files, +64/−20 | n/a | Open |

#233 is over our 10-file limit. Every query that reads `class_enrollments` (roster, hunts, profile, leaderboard, and the three enroll routes) had to filter on the new status in the same PR, or removed students would have kept showing up. About half the files are tests, and it's under 500 lines. I split the frontend part into a second PR to keep it from getting larger.

CI still can't start because of the billing lock, so the test results below are local runs, as agreed in week 9.

**Claim labels.** *Observed* means I ran it or saw it (test output, review text). *Generated* means AI-written code that I reviewed.

---

## 2. PR #232: Shared frontend fetch helper

Frontend: `src/frontend/src/api/request.ts` (new), `joinClass.ts`, `ongoingGames.ts`, `profile.ts`, `answer.ts`

- [x] As part of the refactor plan, every API file repeated the same checks: no connection, an ended session (401) and a failed request. Therefore, I added `apiRequest(url, options, errors)`, and my four student API files now use it. A 401 throws SessionEndedError so the page goes back to login, other statuses use the file's own messages, and `useDetail` shows the backend's message when it has one (for example why a photo was rejected).
- [x] Every message students see stayed the same, except that a dropped connection now says "Could not connect, please try again" instead of the browser's raw "Failed to fetch".
- [x] `login.ts` keeps its own handling, because there a 401 means "Wrong email or password", not an ended session.
- [x] Limitation: the other API files (Madiba's `teacher.ts`, Gamu's `game.ts`, `badges.ts`, `clue.ts`) still have their own checks. They can switch over in their own PRs.
- [x] Tests (observed): 9 new cases in `tests/frontend/apiRequest.test.ts`, covering success, 401, 404/409/503, backend message on and off, a missing message, and no connection. The existing join class, ongoing games, My classes and photo answer tests pass unchanged, which shows the four files behave the same. `npm test`: 24 files, 208 tests passed; `tsc --noEmit` clean; `npm run build` succeeds.

---

## 3. PR #228: Teacher clue audio form

Frontend: `src/frontend/src/components/ClueAudioForm.tsx` (new), `src/frontend/src/api/teacherLocations.ts` (new), `teacher.ts`, `TeacherDashboard.tsx`

- [x] As part of #201, a teacher needs to see which locations in their class's language have audio and upload an MP3 for any of them. #202 (week 9) added the backend. Therefore, this PR adds a Clue audio section to the teacher dashboard: a location list with "Has audio" or "No audio yet", a location dropdown, a file picker and an upload button that says "Replace audio" when a clip exists.
- [x] When I reviewed the generated API file, it copied the login, teacher-access and connection checks from `teacher.ts`. Therefore, I exported the existing `classResponse` helper from `teacher.ts` and reused it instead.
- [x] A note under the form says clips are shared by every class using that location, since that's how #202 stores them.
- [x] Limitations: uploads are Basic clips only (a difficulty on uploads is the next PR), only French has locations, and the form's clicks aren't tested because we have no DOM testing library yet.
- [x] Tests (observed): 11 new cases in `tests/frontend/clueAudio.test.ts` for listing, uploading as the raw body, 403/404/413/422/503, expired session and no connection. `npm test`: 24 files, 210 tests passed; `tsc` clean; build succeeds.

---

## 4. PR #230: One shared role check

Backend: `src/backend/auth.py`, `admin.py`, `teacher_access.py`, `student_enrollment.py`

- [x] As part of the refactor plan, `require_admin`, `require_teacher` and `require_student` were three near copies in three files. Therefore, I added `require_role(role)` next to `current_user` in `auth.py` and built all three from it once. The other modules import the shared ones, so files importing from them keep working and test overrides still apply.
- [x] While doing this I found that login and `/me` crashed with a 500 if an account's role had no dashboard. Therefore, I added `dashboard_for(role)`, which returns 403 "This account cannot sign in" before any session or cookie is created. The database only allows the three roles today, so this is a safety net for adding a new role later.
- [x] Admin routes now say "Admin access required" instead of "Forbidden", matching the other two roles. The admin page already showed that text for a 403, so nothing changed on screen.
- [x] Limitation: about 15 feature files still import the role checks through `admin`, `teacher_access` and `student_enrollment`. Moving them to import from `auth` directly would have made the PR too large.
- [x] Tests (observed): 9 cases in `tests/backend/test_role_access.py` (each role let through, other roles refused, features share the same objects, admin routes refuse students and teachers) and 2 in `test_auth.py` for an unknown role. `pytest tests/backend`: 835 passed.

---

## 5. PR #233: Keep enrollments when a student is removed

Backend: `src/backend/migrations/012_soft_unenroll.sql` (new), `src/backend/utils/enrollment.py` (new), `class_enrollment.py`, `admin_enrollment.py`, `student_enrollment.py`, `class_roster.py`, `student_hunts.py`, `student_profile.py`, `student_leaderboard.py`

- [x] As part of #113, the team decided teachers and the university need records of participation, so removing a student from a class should not delete their data. Therefore, removing a student now sets `status = 'unenrolled'` and `unenrolled_at`, instead of deleting the row. Only an admin deleting the account removes the data.
- [x] The migration adds a check so `unenrolled_at` is set exactly when the status is `'unenrolled'`. I used a status column rather than a lone date so we can add other states later.
- [x] Adding a removed student back (by teacher, admin, or the class code) brings back the same row and keeps the first `enrolled_at`. This is one shared insert-or-update helper in `utils/enrollment.py`, used by all three routes, so two requests at the same time still can't make two rows.
- [x] A removed student no longer sees that class's hunts, the class leaves their profile, and they're left off and blocked from the class leaderboard (403).
- [x] Limitation: in this PR removed students just leave the roster. The open follow-up PR shows them under "Removed students" with their removal date.
- [x] Tests (observed): new tests for removing, re-adding, rejoining by code, removing twice (404), and the roster, hunts, profile and leaderboard leaving removed students out. `pytest tests/backend`: 830 passed against a fully migrated database.

---

## 6. Deploying the app for the demo

Not a PR, but it's most of what moved us towards the demo this week.

- [x] I spent time during the week working out how to deploy the app on hosting services, so we have a working version to demo instead of only running it on our own laptops.
- [x] I got the full system running on my home laptop with Docker Compose (frontend, backend and Postgres) and exposed it on my own domain through a Cloudflare Tunnel. The tunnel connects outwards, so nothing on my home network has to be opened, and Cloudflare gives HTTPS, which the browser needs before it will allow the camera and GPS. (Observed: I opened the site through the domain, logged in, and checked the tunnel's status with `journalctl -u cloudflared`.)
- [x] For quick tests over a temporary `trycloudflare.com` link, Vite blocks unknown hosts, so it needs `allowedHosts: ['.trycloudflare.com']`. That change is only local for now.
- [x] I wrote a seed script and setup notes for the demo server (`temp/week-10/demo-server-seed.md`): migrations, the French locations and GPS targets, an admin, a teacher with classes and a hunt, and four students with finished games for the leaderboard.
- [x] Limitations: only French has enough locations to start a hunt, live answers need GPS within 50 m of the room so they only work on campus, and the server runs on my home laptop, so it's only up while that laptop is. The demo passwords need to change, or the server comes down, after the demo.

---

## 7. Reviews I gave

| PR | Author | What I found | Outcome |
|---|---|---|---|
| #223 Assigned hunts on student dashboard | Gamu | No bugs. README wasn't updated. Play starts a new, unlinked game each time so a hunt never shows as done, which is fine for the demo but needs a follow-up ticket. Suggested switching to `apiRequest` once #232 merged | Merged |
| #227 Dead code, shared password limit, badge rename | Gamu | No bugs. The deleted `admin_reassign.py` was dead and its `require_admin()` returned `True` for everyone. `teacher_signup.py` still had its own `72` and a different message | Merged |
| #236 Camera hook | Dan | Compared the hook with the removed page code and it's a straight move. The PR description skipped the template (no issue link or test results). Ran `npm test` on request: 23 files, 199 tests passed | Merged |

---

## 8. How this fits the overall system

With no assigned tasks this week, the work went into making the code easier to change before the demo and into getting the demo running. #232 and #230 each replace repeated code with one shared piece, so session handling on the frontend and role checks on the backend now change in one place. #228 finishes the teacher side of clue audio that #202 started. #233 changes the class data model so removing a student keeps their history, which the roster, hunts, profile and leaderboard now respect. The deployment means the team can demo the real system from a public HTTPS address on phones.

Next week is the Milestone 1 demo. I plan to merge the roster follow-up for #113, add a difficulty to audio uploads, and keep the demo server up and seeded.
