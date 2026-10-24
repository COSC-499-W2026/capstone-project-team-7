# Week 6 Individual Log: Dan Rukundo

October 12–18, 2026 | Team 7 | Lost In Translation

## Summary

This week I merged three PRs into `main`: shared difficulty definitions, location and translated clue storage, and a refactor of teacher authorization. The first two provide the data and rules needed for the scavenger hunt; the third removes duplicated session checks from my earlier teacher endpoints.

| PR | Issue | Final merged size | Reviewers | Merge commit |
|---|---|---|---|---|
| [#88: Define and validate game difficulties](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/88) | [#86](https://github.com/COSC-499-W2026/capstone-project-team-7/issues/86) | 3 files, +94/−0 | Gamu, Ashish | `a4a477f` |
| [#92: Location and translated clue storage](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/92) | [#91](https://github.com/COSC-499-W2026/capstone-project-team-7/issues/91) | 3 files, +148/−2 | Gamu, Koes | `6283d3d` |
| [#95: Reuse shared authentication](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/95) | [#94](https://github.com/COSC-499-W2026/capstone-project-team-7/issues/94) | 5 files, +51/−43 | Ashish, Gamu | `f3cb3e1` |

Sizes above are the final GitHub PR totals, including tests and documentation. Function lengths below count from the `def` line through the last line of the function, including docstrings. CI results refer to the linked merge commits; local verification is recorded separately.

## PR #88: Define and validate game difficulties

**Requirement and implementation.** The game needs three consistent levels: Basic supplies a room number, Advanced supplies a number and description, and Expert supplies only a description. I added `src/backend/difficulties.py` with a string enum, a frozen `ClueRules` dataclass, and one mapping of levels to content rules. `get_clue_rules()` accepts a supported enum or string and rejects unsupported values rather than silently choosing a default.

**Review findings.** [Ashish questioned why Advanced includes both a number and a description](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/88#discussion_r4300251218). We discussed the structure in a group meeting and confirmed the expected progression; he then approved. [Gamu approved and reported all 19 difficulty tests passing locally](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/88#pullrequestreview-5554670426). This clarified the intended language skills before the rules are used by the hunt logic.

**Code quality and architecture.** The module is 28 lines and `get_clue_rules()` is 3 lines. A single mapping avoids repeated conditionals across future clue consumers, and frozen rule objects prevent callers from changing their flags. The mapping itself is a private dictionary, not an immutable container. This is a shared backend rule module; it adds no route, database migration, audio generation or running game session. `docs/design/game-difficulties.md` documents the boundaries and examples.

**Tests.** `tests/backend/test_difficulties.py` contains 19 parameterized cases:

- Positive: all three levels produce the expected number/description flags; enum and string lookup agree; Pydantic validates and serializes each supported level.
- Negative: unknown values, incorrect capitalization, surrounding spaces and invalid types are rejected; modifying a frozen rule raises `FrozenInstanceError`.
- These are unit tests and require no database. A local rerun against the final `main` snapshot passed: **19 passed**.

**Regression evidence.** Both jobs passed at merge commit `a4a477f`: [backend CI](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/39087330091/job/117556536290), [frontend CI](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/39087330091/job/117556536574).

## PR #92: Location and translated clue storage

**Requirement and implementation.** A hunt needs campus rooms and clues in the teacher's chosen language. I added the new numbered migration `src/backend/migrations/003_locations_and_clues.sql`, leaving earlier migrations unchanged. `locations` stores a generated UUID, building and room number. `location_clues` stores number and description text for each location/language pair and references the existing `languages` table.

The database rejects null, empty and space-padded content, duplicate rooms within a building, duplicate translations, and references to unknown locations or languages. Deleting a location cascades to its clues. Keeping both text fields in storage lets the difficulty rules decide which content a future hunt presents.

**Review findings and changes.** [Koes requested changes](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/92#pullrequestreview-5555106534) covering UUID availability, brittle language-count assertions, and a possible language index. I addressed these in commit `98ad757`:

- Documented PostgreSQL 17's built-in `gen_random_uuid()` and added a test checking automatically generated, distinct version-4 UUIDs.
- Replaced the assumption that there must be exactly six language rows with a check for the six required codes. Migration-repeatability and cascade tests now compare language data before and after the operation.
- Documented that the composite primary key supports location-based lookup. A language-only index is deferred until a query needs it and would be added through a new migration.

[Koes approved after those changes](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/92#pullrequestreview-5566015160). Gamu also approved, highlighting the database constraints and Japanese text coverage.

**Code quality and architecture.** The migration is 14 lines. The test helpers `location()` and `clue()` are 3 and 7 lines respectively; the new location/clue test functions range from 5 to 10 lines. Parameterized tests share setup instead of repeating inserts. SQL values use query parameters. Constraints enforce storage rules for every database writer, rather than relying on a future endpoint to enforce them. `docs/design/location-clues.md` explains the schema and indexing decision.

This contributes the hunt's location/clue data store. It does not seed campus rooms or translations, add management endpoints, select five random rooms, generate audio, or implement GPS verification. Those still need to connect this storage to a running hunt.

**Tests.** `tests/backend/test_database.py` adds **25 location/clue integration cases**, plus a supported-language seed test and revised repeatability checks. The final count includes UUID coverage and null-reference cases; it is larger than the original PR description's 24 cases.

- Positive: generated UUIDs, French and Japanese clues on the same location, the same room number in different buildings, and alphanumeric room numbers.
- Negative: invalid text, duplicate rooms and translations, null references, and unknown location/language references raise the expected PostgreSQL constraint errors.
- Cascade: deleting one location removes its clues while preserving another location's clues and the language records.
- These tests use real PostgreSQL with temporary schemas and transaction cleanup. They verify persistence and constraints rather than mocked SQL behavior.

**Regression evidence.** Both jobs passed at final merge commit `6283d3d`: [backend CI](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/39185384008/job/117846614904), [frontend CI](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/39185384008/job/117846614680). Backend CI provisions PostgreSQL 17 and sets both database URLs for integration tests.

## PR #95: Reuse shared authentication in teacher endpoints

**Problem and implementation.** My class-access and teacher-approval endpoints repeated cookie extraction, token hashing and session SQL that the shared authentication module already provided. I changed `src/backend/teacher_access.py` to obtain the teacher through `require_teacher` and `auth.current_user`, and changed `src/backend/teacher_approval.py` to use `Depends(require_admin)`. This keeps session validity and role checks consistent with the team's other protected endpoints.

Invalid sessions now use the shared 401 `Unauthorized` response; non-admin approval requests use 403 `Forbidden`. Authentication runs before approval body validation, so an unauthenticated request with invalid input receives 401. The README records this behavior.

**Review findings and code quality.** This resolves the duplicate session-check code identified in the earlier teacher work and noted in Ashish's class-creation work. [Ashish approved and confirmed the tests still passed locally](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/95#pullrequestreview-5560373516); Gamu also approved the removal of duplication. I removed the unused hashing and request imports with the old checks.

The final `teacher_connection()` is 6 lines, compared with 18 before this refactor; `approve_teacher()` is 12 lines, compared with 24 before. The final modules are 84 and 38 lines respectively. The connection dependency now opens the feature connection and translates database failures; shared dependencies handle identity and role checks. Existing class queries still filter by the authenticated teacher's ID.

**Tests.** I updated `tests/backend/test_teacher_access.py` and `tests/backend/test_teacher_approval.py` to test failures at the correct layer:

- Authentication failures patch `auth.get_connection`, where session lookup now happens.
- Two new class-read cases check safe 503 responses for list and detail queries after successful authentication.
- A new approval-insert failure case checks a safe 503 after the admin dependency succeeds.
- Missing approval sessions are rejected before either connection opens. Invalid-body unit tests override the authenticated user so they isolate validation, and dependency overrides are cleared after each client fixture.
- Existing integration tests retain positive class access and approval-to-signup coverage, plus negative ownership, role and expired-session coverage.

**Regression evidence.** Both jobs passed at merge commit `f3cb3e1`: [backend CI](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/39148828030/job/117738102715), [frontend CI](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/39148828030/job/117738102574).

## Reviews and collaboration

I submitted approvals on Ashish's [class creation #76](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/76#pullrequestreview-5551882875), [teacher enrollment #78](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/78#pullrequestreview-5554410366), [student removal #80](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/80#pullrequestreview-5554835174), and [self-enrollment #89](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/89#pullrequestreview-5560537311). My #76 review noted success/error-path coverage. On #80, I accepted the clarification that the added lines were needed for tests. These were approvals; my recorded reviews did not request code changes.

I also resolved the difficulty-design question with Ashish and implemented Koes's storage review requests before merging. The shared-auth refactor preserves the teacher class functionality that Ashish extended, while removing the duplicate authentication from my original implementation.

## Verification and next steps

On October 18, I checked the final merged diffs, GitHub reviews, and successful backend/frontend CI jobs for all three PRs. Local verification used an exported `main` snapshot at `6283d3d` so the separate `weekly_logs` branch was not mistaken for the implementation under test. The difficulty suite passed all 19 cases. The full backend attempt stopped with 12 collection errors because the local environment lacks `email-validator`; frontend `npm test` could not start because `vitest` was unavailable in the exported snapshot. Full regression evidence above comes from GitHub CI, not a successful local full-suite run.

The next step is to connect the difficulty rules and translated location data to game-session creation and clue selection. Local dependency setup also needs to be completed before the full suites can be rerun locally.

## Correction to my Week 5 report

My previous #45 section described an intermediate version. The [merged teacher-signup PR](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/45) has **197 added lines across four files**, and retains automated persistence, unauthorized-signup and duplicate-signup tests. Ashish requested happy-path coverage and Gamu requested unauthorized coverage, with duplicate coverage suggested; the final changes received approval. The earlier claims of 118 lines and removed database tests were incorrect. That work belongs to Week 5 and is not included in this week's contribution totals.
