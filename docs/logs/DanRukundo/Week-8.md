# Week 8 Individual Log: Dan Rukundo

October 26–November 1, 2026 | Team 7 | Lost In Translation

## Summary

This week I connected last week's GPS validator to the game, added browser location capture to photo submission, and implemented points based on difficulty and photo attempts. All three PRs are merged into `main`. Students now need an acceptable GPS reading before their photo is checked, and a correct answer earns fewer points after repeated attempts.

| PR | Issue | Final GitHub PR size | Status |
|---|---|---|---|
| [#154: Validate location when submitting answers](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/154) | [#152](https://github.com/COSC-499-W2026/capstone-project-team-7/issues/152) | 5 files, +120/−8 | Merged |
| [#155: Capture and send GPS with photos](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/155) | [#153](https://github.com/COSC-499-W2026/capstone-project-team-7/issues/153) | 11 files, +240/−13 | Merged |
| [#178: Difficulty- and attempt-based points](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/178) | [#176](https://github.com/COSC-499-W2026/capstone-project-team-7/issues/176) | 6 files, +176/−19 | Merged |

#155 includes #154's backend commit in its GitHub totals; these sizes should not be added together as separate contributions. Its frontend commit alone changes seven files, with 122 additions and seven deletions.

## PR #154: GPS validation on answer submission

**Requirement and implementation.** The game must check that a student is near the current target before accepting a room photo. I updated `POST /api/game/{game_id}/answer` to require latitude, longitude, accuracy and capture time, and added `utils/answer_location.py` to connect the existing proximity validator to the answer flow.

The server loads the active target's coordinates rather than accepting target coordinates from the browser. The existing student authentication and game-ownership checks remain in the route. GPS validation runs before photo recognition. Stale, inaccurate or out-of-radius readings return a friendly 422 response without changing attempts, points or progress. An unconfigured target returns 503. The README documents the request fields and target setup.

**Review and collaboration.** [Ashish approved with a merge-order warning](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/154#pullrequestreview-5692167063): requiring GPS before the frontend sent it would make the game unplayable. I kept the frontend work in #155, which carries this backend dependency. [Gamu approved](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/154#pullrequestreview-5692461282), highlighting server-owned coordinates and unchanged points after rejected readings.

**Code quality and tests.** I reused `LocationReading`, `ProximityTarget` and `check_proximity` rather than duplicating coordinate or distance rules. The small adapter handles target configuration and user-facing rejection messages separately from the route. No migration or dependency was needed. The implementation records 61 passing GPS/game tests, including acceptance and rejected readings. Final head `5d9ce7d` passed [CI](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/40632394153).

## PR #155: Browser GPS capture with each photo

**Requirement and implementation.** I added `api/location.ts` and connected it to the existing photo-upload request. Each submission requests a fresh, high-accuracy browser location with `maximumAge: 0` and a ten-second timeout, then sends the coordinates, accuracy and timestamp with the photo. The photo page shows location guidance and keeps the photo available for retry if location capture fails.

Denied permission, timeout, unavailable location and unsupported browsers produce specific messages. The browser collects the reading; the backend decides whether it is acceptable. The README explains HTTPS/localhost requirements and local GPS testing.

**Review and changes.** Gamu asked for screenshots, which I added to the PR description. [Her approval records a laptop check with simulated coordinates](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/155#pullrequestreview-5692474201). [Ashish also completed all five locations using simulated GPS](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/155#pullrequestreview-5719637874). Both identified real-phone accuracy and the campus radius as follow-up work. These checks establish the browser flow, not reliable indoor room or floor detection.

**Code quality and tests.** Location capture lives in its own API helper and reuses the existing submission flow. The timeout is a browser wait limit, not an arrival radius; arrival rules stay on the server. Frontend tests cover sending location fields and capture failures, alongside photo-page coverage. The implementation records **50 frontend tests passed** and a successful production build. Final head `45e3f30` passed [CI](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/40634481376).

## PR #178: Points by difficulty and attempts

**Requirement and implementation.** I replaced flat location points with a shared helper in `utils/scoring.py`. The backend reads the game's stored difficulty and the current location's attempt count. Incorrect photos earn zero; correct photos earn:

| Difficulty | First attempt | Second attempt | Third or later |
|---|---|---|---|
| Basic | 10 | 6 | 3 |
| Advanced | 20 | 12 | 6 |
| Expert | 30 | 18 | 9 |

The first attempt earns 100%, the second 60%, and subsequent attempts 30%. GPS rejections do not count as photo attempts. Unsupported stored difficulties return a friendly 500 before attempts, points or progress change. The README records the final scoring rules.

**Review findings and changes.** My initial version varied points only by difficulty. [Gamu requested attempt-based scoring](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/178#pullrequestreview-5719451523), since otherwise everyone finishing the same difficulty would receive the same total. I incorporated her proposed 100%/60%/30% rule and updated the tests and documentation.

After merging `main` into the branch, I found and removed a duplicate attempts update that would have counted each photo twice. The final fix also updates the fake-database expectations in the answer tests. [Gamu approved the scoring and duplicate-update fix](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/178#pullrequestreview-5732010675); Koes also approved before merge.

**Code quality and tests.** Two small scoring functions separate difficulty lookup from attempt reduction. Point values are defined in one table, and the route reuses existing difficulty and attempt storage without a migration. Positive and negative tests cover difficulty awards, incorrect photos, unsupported difficulty, repeat attempts and invalid attempt numbers.

The initial implementation records **60 targeted backend tests passed** against PostgreSQL 17 and **55 frontend tests passed**. Its first full backend run had 563 passes and five failures caused by missing migrations in the temporary database; those five passed after migrations were applied. These counts predate the attempt-based revision. Final head `713e53d` passed [CI](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/41381556887). The team log separately records the merged `main` run at `3a31aa5`: **674 backend tests and 122 frontend tests passed**.

## Reviews and collaboration

I approved the following teammate PRs this week. Most approvals were brief; I am not claiming additional testing or findings beyond the recorded review.

| PRs | Area | Recorded contribution |
|---|---|---|
| #160, #164 | Create-account demo and design documentation | Approved the demo and docs updates |
| #161, #163 | Badge rules and badges endpoint | Approved both parts |
| #165 | Teacher-assigned hunts | Approved the endpoints |
| #167, #169 | Stopwatch and audio storage | Approved both changes |
| [#171](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/171#pullrequestreview-5709042920) | Resume unfinished games | Approved and suggested an interaction test proving Resume opens the selected game; existing coverage only checked the rendered button |
| #173, #184 | Teacher dashboard work | Approved the dashboard PRs |
| #177 | Faster tests and CI | Approved the refactor |
| #180, #182 | Join a class and list enrolled classes | Approved both frontend changes |
| #188 | Teacher class roster | Approved the teacher demo addition |

## Verification and accomplishments

All three contributions were completed, reviewed and merged into `main` during this reporting week. I checked the successful backend tests, frontend tests and production-build steps for each final PR head:

| PR | Final head | Backend tests | Frontend tests and build |
|---|---|---|---|
| #154 | `5d9ce7d` | [Passed](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/40632394153/job/122631554104) | [Passed](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/40632394153/job/122631553491) |
| #155 | `45e3f30` | [Passed](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/40634481376/job/122638163748) | [Passed](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/40634481376/job/122638163430) |
| #178 | `713e53d` | [Passed](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/41381556887/job/125073275188) | [Passed](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/41381556887/job/125073275339) |

The integrated `main` run at merge commit `3a31aa5` also passed [backend regression tests](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/41388304842/job/125093941177) and [frontend tests and build](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/41388304842/job/125093941320). The team log records 674 backend tests and 122 frontend tests for that run. The earlier temporary-database failures described above were resolved before the final successful CI runs.

This week's goals are accomplished: GPS is connected from browser capture through backend answer validation, and correct answers receive server-calculated points based on difficulty and attempts. The real-device checks and additional features below are future work.

## Architecture and next steps

This work completes the GPS data flow in the Play Game process: browser location and photo → authenticated answer endpoint → server-owned target validation → photo recognition → attempts, points and progress. Scoring remains a server decision and uses the existing game records. GPS capture, location acceptance and scoring stay in separate helpers, although `game_session.py` remains a shared integration point that needs attention as more features arrive.

The team demonstrated the game to the TA on October 29. Follow-up work is to tune the location check and investigate elevation. GPS can be spoofed and does not prove the student's room or floor; the simulated browser checks do not settle campus accuracy. Games also still start in French on Basic difficulty, so language and difficulty selection are needed to expose the other scoring levels through the normal frontend. Points redemption and the leaderboard can build on the scoring now in place.
