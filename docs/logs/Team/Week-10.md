# Week 10 Team Log: Team 7

Authors: Ashish, Dan, Gamu, Madiba

November 9–15, 2026

## Bonus week

This was reading week, so it was a bonus week. We didn't assign sprint tasks. Instead, we agreed that whoever had time would work through the refactor plan from November 6 and anything else that moves the app towards the Milestone 1 demo after the break.

## PRs covered

| PR | Author | What | Size | Status |
|---|---|---|---|---|
| [#223](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/223) | Gamu (gamurrrrr) | Assigned hunts on the student dashboard, with a Play button per hunt | 4 files, +168/−1 | Merged |
| [#227](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/227) | Gamu (gamurrrrr) | Remove dead admin code, share the password limit, rename the Polyglot badge, fix OCR on x86 and Windows | 9 files, +20/−51 | Merged |
| [#228](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/228) | Ashish (nayakashish) | Teacher dashboard form to upload clue audio | 6 files, +177/−1 | Merged |
| [#230](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/230) | Ashish (nayakashish) | One shared `require_role` check, and no 500 for a role with no dashboard | 7 files, +102/−27 | Merged |
| [#232](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/232) | Ashish (nayakashish) | Shared frontend fetch helper `apiRequest` | 8 files, +104/−28 | Merged |
| [#233](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/233) | Ashish (nayakashish) | Keep a student's enrollment when they're removed from a class | 18 files, +141/−34 | Merged |
| [#236](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/236) | Dan (danruk) | Move the camera code out of PhotoSubmitPage into a `useCameraCapture` hook | 3 files, +84/−72 | Merged |
| Roster removed students | Ashish (nayakashish) | Show removed students and their removal date on the roster (#113, part 2) | 7 files, +64/−20 | Open |

All seven merged PRs went into `main` between November 13 and 14 (`5965eaf` to `7fc2251`). #233 is over our 10-file limit. Each query that reads class enrollments had to respect the new status in the same PR, or removed students would still show up. The frontend half was split into the open roster PR so #233 didn't grow further.

## Goal and work distribution

- **Goal:** use the reading week to make the code easier to change before the demo (refactor plan), finish small demo gaps, and get a working deployment we can demo from.
- **Ashish** did three rows of the refactor plan: the shared fetch helper (#232), one shared role check (#230) and the unknown-role crash (#230). He finished the teacher audio form (#228) that his week 9 API (#202) needed, and did the backend for keeping removed students' data (#233), with the roster screen open as a follow-up. He also worked out how to deploy the app on hosting services. He got the full system running on his own domain from his home laptop through a Cloudflare Tunnel, and wrote seed data for the demo server.
- **Gamu** added assigned hunts to the student dashboard (#223), so students can see and start hunts their teacher assigned. Her refactor PR (#227) deleted the unused `admin_reassign.py` route and moved the 72-byte password limit to one place. It also renamed the Polyglot badge without changing its id, installed `libgomp1` in the backend image so OCR runs on x86 machines, and fixed the OCR tests on Windows.
- **Dan** moved the camera start, stop, capture and retake code out of `PhotoSubmitPage.tsx` into the new `useCameraCapture` hook (#236), so the page only handles layout.

**Alternative distributions.** We considered assigning a normal sprint for the break. We didn't, because members had different availability over reading week. A shared refactor list let anyone pick up a small, separate item without blocking someone else.

**Did we meet the goal?** Since it wasn't a normal week, we agreed there was good progress regardless. Seven PRs merged, four of them refactors from the plan. Teachers can now upload clue audio from the dashboard instead of only through the API. Students see their assigned hunts. Removing a student keeps their history. We also have a public HTTPS deployment the demo can run from. Still open: the removed-students roster PR, other API files switching to `apiRequest`, hunts linked to games, and a full regression run on the integrated app.

## Code-base health

The refactor plan was built by reading through the code for repeated logic. This week found and fixed these:

- **Similar logic in many places.**
  - Ashish found three near-copy role checks in `admin.py`, `teacher_access.py` and `student_enrollment.py`. #230 builds all three from one `require_role` in `auth.py`.
  - Every frontend API file repeated its own offline, 401 and error handling. #232 adds `apiRequest`, and four student API files use it.
  - The teacher, admin and join-by-code routes each enrolled students their own way. #233 replaces them with one `utils/enrollment.py` helper.
  - The 72-byte password limit was defined in more than one place. #227 moves it into `utils/passwords.py`.
- **Dead and risky code.** Gamu removed `routes/admin_reassign.py`, which was never added to the app and whose `require_admin()` let everyone through (#227). The real reassign route in `admin.py` stays.
- **Components with more than one job.** Dan moved the camera lifecycle out of `PhotoSubmitPage.tsx`, which drops from about 140 lines to 75 (#236). This is the frontend's first `hooks/` folder.
- **Changes in one component requiring changes elsewhere.** Before #230, changing how roles are checked meant editing three files. Now it's one. #233 is the opposite case: adding enrollment status meant changing every query that reads enrollments, which is why it touched 18 files.

**Known debt.**
- About 15 feature files still import role checks through `admin`, `teacher_access` and `student_enrollment` instead of from `auth`.
- `teacher.ts`, `game.ts`, `badges.ts` and `clue.ts` still have their own fetch checks.
- `teacher_signup.py` still has its own 72-byte check.
- Playing an assigned hunt starts a normal game that isn't linked to the hunt, so a hunt never shows as done.
- Clue audio uploads are Basic only and shared by every class using a location.

These are all known changes by our team and we will work through them as time between team members permits. 

## Testing and validation

These results come from the PR descriptions and reviews. Each was run on that PR's branch, so they are not one final regression run as the organization CI still fails.

| Check | Command | Recorded result |
|---|---|---|
| Role check (#230) | `python -m pytest tests/backend` | 835 passed |
| Soft unenroll (#233) | `python -m pytest tests/backend`, fully migrated database | 830 passed |
| Fetch helper (#232) | `npm test`, `tsc --noEmit`, `npm run build` | 24 files, 208 tests passed; clean; builds |
| Clue audio form (#228) | `npm test`, `tsc --noEmit`, `npm run build` | 24 files, 210 tests passed; clean; builds |
| Student hunts (#223) | `npm test` | 207 tests, 8 new |
| Dead code and badge rename (#227) | `python -m pytest tests/backend` | 446 passed, 1 new |
| Camera hook (#236) | `npm test`, `tsc --noEmit`, `npm run build` (run by Ashish in review) | 23 files, 199 tests passed, same as `main`; clean; builds |

Each PR had positive and negative tests:
- #230: each role is let through its own check, and other roles get 403.
- #233: removing, re-adding and rejoining a student, removing twice (404), and removed students left out of the roster, hunts, profile and leaderboard.
- #232: success, 401, other failures, the backend message on and off, and no connection.
- #228: uploading, 403/404/413/422/503, expired session and no connection.
- #223: the API, 401, 503, no connection, past-due hiding and the empty list.
- #236: the camera error messages, with only the import changed, which shows the page behaves the same.

**CI limitation.** GitHub Actions still can't start jobs because of the billing lock, so none of these have a passing CI run. As agreed in week 9, we rely on local runs and will fix anything CI finds once it runs again.

**Deployment check.** The full app (frontend, backend, Postgres in Docker Compose) runs on Ashish's home laptop and is reached through his domain over a Cloudflare Tunnel. The tunnel gives HTTPS, which phones need before allowing the camera and GPS. Limits:
- The server is only up while that laptop is.
- Only French has enough locations to start a hunt.
- Live answers need GPS within 50 m of the room.
- The demo logins must be changed, or the server taken down, after the demo.

This is a temporary hosting method for the demo adn we will begin work to get it hosted on UBC servers after the demo. 

## Architecture and DFD alignment

With this week's merged work, the system architecture and DFDs are the same as in week 9.

- **Why the DFDs are the same.** The refactors (#230, #232, #236, #227) move code without changing any data flow. #233 changes what happens in the class data store: removal now updates an enrollment's status instead of deleting it. But the Class DFD's processes and flows are unchanged, since "remove student" still writes to the same store. #223 shows students hunts from the "view assigned hunts" flow that was already drawn in #193. #228 is the frontend for the teacher audio upload that #202 already added to the backend.
- **Why the architecture is the same.** No new components or dependencies were added to the app. `libgomp1` is a system library PaddleOCR already needed. The Cloudflare Tunnel is how we host the demo, not part of the system's design, so we left it out of the diagram for now. If the team keeps that deployment after the demo, we'll add it as a hosting box in front of the frontend and backend.
- **Alternatives considered.**
  - For #233, deleting the enrollment and keeping a separate history table. We kept one row with a status instead, so re-adding a student brings back the same enrollment and its first enrolled date, and no new data store is needed.
  - For deployment, hosted services. Running it from a home laptop over a tunnel was free, needed no changes to the app, and gave HTTPS without opening the home network.

## Collaboration process and next steps

Next week is the Milestone 1 demo. We need to:
- merge the removed-students roster PR to close #113
- add a difficulty to clue audio uploads
- link assigned hunts to games
- walk the student, teacher and admin demo paths on the deployed server, including GPS and OCR on real phones on campus
- make any final changes we want to be demo'd
