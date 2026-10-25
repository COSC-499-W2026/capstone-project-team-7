# Week 7 Individual Log: Dan Rukundo

October 19–25, 2026 | Team 7 | Lost In Translation

## Summary

This week I implemented and merged three backend PRs into `main`: GPS proximity validation, demo target coordinate configuration, and an endpoint returning the signed-in student's profile. The GPS work provides the location checks and target data needed for future answer verification; the profile endpoint connects existing account, enrollment and language records without adding a new schema.

| PR | Issue | Final merged size | Reviewers | Merge commit |
|---|---|---|---|---|
| [#134: Backend GPS proximity validation](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/134) | [#106](https://github.com/COSC-499-W2026/capstone-project-team-7/issues/106) | 6 files, +163/−1 | Koes, Ashish, Gamu | `6732e26` |
| [#137: Demo target coordinates and arrival radius](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/137) | [#135](https://github.com/COSC-499-W2026/capstone-project-team-7/issues/135) | 3 files, +122/−0 | Gamu, Koes | `7df72da` |
| [#140: Student's own account details](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/140) | [#105](https://github.com/COSC-499-W2026/capstone-project-team-7/issues/105) | 4 files, +164/−0 | Gamu, Koes | `0cfc211` |

Sizes are the final GitHub PR totals, including tests and documentation, rather than intermediate local counts. CI links below refer to the final PR head commits. Local runs used different implementation snapshots as the work progressed; their totals are recorded separately.

## PR #134: Backend GPS proximity validation

**Requirement and implementation.** The game needs to check whether a student's reported position is near the active target before accepting an answer. I added `src/backend/proximity.py` with validated coordinate, location-reading and target models, a Haversine distance calculation, and a reusable `check_proximity()` function.

The validator rejects out-of-range coordinates, non-finite numbers, non-positive accuracy/radii and timestamps without a timezone. A reading older than 30 seconds or more than 5 seconds in the future returns `stale_location`. Accuracy worse than the target's radius returns `inaccurate_location`; a distance beyond the radius returns `outside_radius`. A fresh, sufficiently accurate reading inside or exactly on the boundary returns `within_radius`.

The new migration adds latitude, longitude and `radius_metres` to `locations`. Existing targets remain unconfigured until all three fields are supplied together. Constraints reject invalid ranges and incomplete configuration. No campus data is invented or seeded by this migration.

**Review findings and changes.** [Ashish noted that #120 already used migration number 005](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/134#pullrequestreview-5641315438). Although the runner supports different filenames with the same numeric prefix, I renamed the coordinate migration to `006_location_coordinates.sql` and updated both documentation references in commit `df05d82`. This kept the numbering consistent without changing the SQL content.

[Gamu approved and highlighted the need to test indoor accuracy on real phones](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/134#pullrequestreview-5641422716). Koes also approved the validator's scope and edge-case coverage. The acceptable radius remains a campus-testing decision, not a value proven by the automated tests.

**Code quality and architecture.** The validator is a separate 45-line module, with distance calculation separated from acceptance rules. Pydantic models share coordinate validation. The migration adds constraints rather than relying on individual callers to validate database writes. `docs/design/gps-location.md` describes the integration contract and limitations.

This PR is backend-only. It does not collect browser GPS, show a map, track teachers' views, or connect the validator to answer submission. A future handler must authenticate the student, load the server's active target and call the validator. Client coordinates and timestamps can be spoofed, so this check is not proof of physical presence or floor.

**Tests.** `tests/backend/test_proximity.py` contains 20 cases covering valid readings, distance boundaries, stale/future readings, poor accuracy, invalid coordinates, non-finite values and invalid target radii. Eleven new schema cases cover saving target coordinates and rejecting invalid or incomplete configurations.

- Full local backend run with both database URLs configured: **408 passed, none skipped**. An earlier run skipped eight existing integration tests because only `TEST_DATABASE_URL` was configured; these were subsequently run successfully.
- Frontend test and production build passed on that snapshot.
- After renaming the migration: **20 proximity tests and 27 migration/location schema tests passed**; `git diff --check` passed.
- Local integration tests used PostgreSQL 14. CI uses the project's PostgreSQL 17 configuration.

**Regression evidence.** Final PR head `df05d82` passed [backend CI](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/40213715096/job/121230221198) and [frontend CI](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/40213715096/job/121230221045).

## PR #137: Demo target coordinates and arrival radius

**Requirement and implementation.** The validator needs configured target coordinates. Gamu's #123 already supplied five demo locations and coordinates, but its seed script did not save the coordinates. I added `src/backend/utils/seed_target_coordinates.py` to read that existing list and update the matching database rows with their latitude, longitude and a 50-metre arrival radius.

The targets are COM 316, LIB 312, ASC 130, LIB 317 and ART 376. These remain provisional demo targets. The 50-metre radius is an initial setting for on-site testing, not a verified floor- or room-level tolerance.

**Review findings.** [Gamu approved the reuse of the existing coordinate list and the rollback behavior](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/137#pullrequestreview-5641462455). [Koes approved without requesting edits](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/137#pullrequestreview-5644232452).

**Code quality and architecture.** The updater is 29 lines and uses parameterized updates inside one transaction. It does not duplicate the demo location list, add a migration, create targets or change translated clues. A missing target raises an error and rolls back the batch. Repeated runs preserve the same rows and values; unrelated locations remain unchanged.

This PR depends on #123's seed list and #134's coordinate columns. `docs/design/demo-target-coordinates.md` records those dependencies, the execution command and the provisional nature of the data. Preparing and testing the updater does not establish that the production/demo database has been populated.

**Tests.** Four database-backed cases check coordinate/radius persistence, repeatability without duplicates, preservation of unrelated targets and rollback after a missing target. Tests use a temporary table matching the expected dependency schema, allowing the updater to be exercised before the dependency branches are integrated.

- Full local backend suite on this branch: **398 passed, none skipped**.
- Frontend suite: **9 passed**; production build passed.
- Local database tests used PostgreSQL 14; CI targets PostgreSQL 17.

**Regression evidence.** Final PR head `37cbf06` passed [backend CI](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/40138086665/job/121003796778) and [frontend CI](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/40138086665/job/121003796609).

## PR #140: Student's own account details

**Requirement and implementation.** Students need their username, enrolled classes, studied languages and profile icon for the profile screen. I added `GET /api/student/profile` in `src/backend/student_profile.py` and registered its router in `main.py`.

The endpoint reuses `require_student` and the shared session authentication. Every query is scoped to the signed-in user's ID. Languages combine explicit `student_languages` records with enrolled-class languages, removing duplicates. Students without classes or study records receive empty lists. Passwords, email addresses, session tokens and student numbers are not returned.

Profile-icon storage is a separate feature and does not yet exist in the schema. I kept this PR focused on retrieval and return `profile_icon: null` until that storage is implemented. Missing/invalid sessions return 401, non-students receive 403, missing student records receive 404 and database failures return a safe 503.

**Review findings and changes.** The initial version also exposed `/profile/{student_id}` but only allowed the caller's own ID. [Gamu pointed out that this duplicated `/profile` without a planned teacher-access use case](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/140#pullrequestreview-5641472507). I removed the redundant route, UUID parameter and ownership comparison in commit `fd1e7dd`. Tests and documentation were updated to match the simpler session-only interface.

ID-based paths now return 404. Supplying a different student ID in a query cannot select another account; the endpoint still queries by the session identity. [Koes approved the scoped access checks and supporting tests/docs](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/140#pullrequestreview-5644228121).

**Code quality and architecture.** The endpoint lives in one feature module and reuses existing auth dependencies rather than repeating cookie/session logic. It reads existing account, class, enrollment and language tables using parameterized queries. No schema changes or dependencies were added. `docs/design/student-profile.md` documents the response and failure cases.

**Tests.** The final profile suite contains 12 cases. Unit tests fake the database and exercise empty profiles, removed ID paths, ignored account-selection attempts, role restrictions, missing/invalid sessions, missing student records and safe database failures. The integration test uses a real temporary schema to check enrolled classes, deduplicated languages and isolation from another student's study records.

- Full backend suite before the final icon and route simplifications: **404 passed, none skipped**.
- After adding `profile_icon: null`: **10 profile tests passed**, including integration.
- After removing the redundant ID route: **12 profile tests passed**, including integration; `git diff --check` passed.
- Frontend tests and production build passed during the initial implementation. The final full regression evidence is the CI run below, rather than a claim that the complete suite was rerun locally after every edit.

**Regression evidence.** Final PR head `fd1e7dd` passed [backend CI](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/40215492021/job/121235615352) and [frontend CI](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/40215492021/job/121235615103).

## Reviews and collaboration

I reviewed the team's demo flow and checked dependency order so stacked changes would be merged after their prerequisites:

- [#120: Start-game endpoint](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/120#pullrequestreview-5636384271): approved the scoped game-start feature.
- [#123: Demo locations and audio](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/123#pullrequestreview-5640862756): approved and reused the same location list in my coordinate updater.
- [#125: Clue/audio endpoints](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/125#pullrequestreview-5641193722): approved with a reminder to merge #120 and #123 first.
- [#127: Game screen](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/127#pullrequestreview-5641206699): approved for the demo and requested a non-blocking follow-up for audio-load failure messages and retry handling.
- [#129: Answer submission](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/129#pullrequestreview-5641235665): approved for the demo with a reminder to merge #125 first.
- [#132: Camera/photo page](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/132#pullrequestreview-5641255587): approved with a reminder to merge #127 first.
- [#133: Submit/finish flow](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/133#pullrequestreview-5641265230): approved with a reminder to merge #132 first.
- [#139: Documentation merge](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/139#pullrequestreview-5644815122): approved the documentation update.

During the #129 review, 31 existing game/answer tests passed in an isolated snapshot. An additional temporary regression test reproduced two identical submissions advancing from spot 1 to spot 3 with the demo's always-correct checker. I also identified that the upload size is checked after the whole request body is buffered. These were discussed as follow-up concerns; my submitted approval only records the dependency reminder, not a claim that either issue was fixed. The review did not change my teammate's branch or PR.

## Verification and next steps

I checked the final PR metadata, approvals and successful CI jobs for all three of my merged PRs when preparing this log. The work kept GPS validation, target configuration and profile retrieval in separate PRs, and incorporated the migration-numbering and redundant-route feedback before merge.

The next backend GPS step is to connect #134's validator to answer submission: accept a student's reading, authenticate ownership of the active game, load its target from the server and prevent advancement when proximity validation fails. Browser GPS collection and the student map remain frontend work. Final campus targets and suitable indoor radii still need confirmation and on-site testing.

I also explored altitude as possible floor evidence. A phone and computer in device mode displayed readings about five metres apart at the same location, so I did not implement a strict altitude-based floor check or treat the website reading as a verified reference. Comparing real phone readings across adjacent floors and devices remains testing work. The existing plan uses GPS for the general area and room-sign recognition for the specific target; neither has been represented as guaranteed proof of floor or presence.
