# Week 4 Individual Log: Gamu

Team 7 | Repo: capstone-project-team-7 | PRs this week: #8 (merged), #19 (merged)

---

## PR #8: Set up GitHub Actions CI for the backend (merged into `dev`)

**Size:** 2 files changed, +43 / -1 lines (`.github/workflows/ci.yml` added, `docs/Proposal/placeholder.txt` deleted).

- As part of the testing and CI/CD requirement, a developer needs to push or open a PR against `dev` or `main` and see the backend PyTest suite run automatically, with a test report they can look at.
- Therefore, I implemented `.github/workflows/ci.yml` so that the dev team gets: automatic backend tests on every push/PR to `dev` and `main`, the test results uploaded as a downloadable artifact, and the latest report saved into `test-reports/` originally (changed in PR #19) after each push to `dev`.

**Review receipts**

- When I reviewed the "Save report into repo" step, I noticed it commits from inside the workflow, which could retrigger the workflow in a loop. Therefore, I added `[skip ci]` to the commit message and limited the step to pushes on `dev`. The step also only runs if the tests passed. 
- The "Save report into repo" step in this PR pushes straight to `dev`, which branch protection blocks (PRs + approvals required). I removed it in PR #19 and kept the artifact upload as the way to get test reports. 
- The PR contains no functions, only one 43-line workflow file with one job.
- Removed `docs/Proposal/placeholder.txt` because it was a placeholder file when setting up initial repo project structure.

**Architecture receipts**

- This file is in `.github/workflows/ci.yml` because GitHub Actions only reads workflows from that folder. It doesn't belong in `src/` or `tests/`.
- This PR belongs in the developer-side "automated testing / CI" flow of the DFD, because it runs on push or PR and returns test results to the developer, and it is outside the app's runtime data flow.

**Clean Code Check** 
- I re-read ci.yml to check for hardcoded values, duplicate code, dead code, deep nesting and unrelated responsibilities. The Python version and the report paths are written once or twice and are acceptable for a single-job workflow.

**Testing receipts**

- This PR adds no new tests. It runs the existing test in `tests/backend`.
- Happy path: a push/PR to `dev` ran the workflow, it went green
- Negative case: the tests failed the CI Actions and a red cross showed.
- Unit/integration: not required, because this PR has no application logic. The Actions run is the verification.
- Test location: `tests/backend`
- Regression: nothing else in the system was affected because only a workflow file was added and a placeholder removed, CI passed:[Backend CI run #36923184982](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/36923184982)

---

## PR #19: Frontend CI and Vitest setup (branch `9-set-up-github-actions-frontend-ci`, into `dev`)

**Size:** 5 files, +318 / -18. 

- As part of the testing and CI/CD requirement, a developer needs to push or open a PR and have the frontend built and tested automatically, the same way the backend is. Therefore, I implemented a `frontend` job in `.github/workflows/ci.yml` (Node 22, `npm ci`, `npm run build`, `npm test`, run from `src/frontend`), a `"test": "vitest run"` script in `src/frontend/package.json`, `src/frontend/vitest.config.ts` so Vitest looks for tests in `tests/frontend`, and a placeholder test `tests/frontend/sampletest.test.ts` so CI has something to run for now
- I also removed the "Save report into repo" step because the team agreed to manually download the test html file after CI runs on a PR.

**Review receipts**

- When I reviewed the backend job from #8, I noticed the report-saving step pushes directly to `dev`, and branch protection blocks that. Therefore, I removed the step. 
- When I reviewed`vitest.config.ts`, I did not find any problems because `npm test` passes locally. 
- This PR contains one deliberate temporary placeholder: `sampletest.test.ts` exists only so `npm test` has something to run until real frontend tests exist. It will be replaced when frontend development begins. Nothing else in the PR is a workaround.
- The PR contains no functions other than the placeholder test.
- I only added the `test` script and the Vitest dependency, and did not change app code.

**Architecture receipts**

- The frontend job is in the existing `ci.yml` (not a new file) because it keeps backend and frontend checks in one workflow that runs on the same triggers. `vitest.config.ts` is in `src/frontend/` next to `package.json` because that is where `vitest run` is executed, and the test is in `tests/frontend/` 
- This PR belongs in the developer-side "automated testing / CI" flow of the DFD, because it runs on push or PR and returns test results to the developer, and it is outside the app's runtime data flow.

**Clean Code Check** 
- I re-read the frontend job, the Vitest config and the sample test for the same issues. The Node version is set in one place, and the PR has no duplicated or dead code.

**Testing receipts**

- Happy path: `npm test` ran the placeholder test and passed locally (per my commit "Added vitest and a sample npm test"). In CI: [Frontend CI job #111536424913](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/37236460783/job/111536424913)
- Negative case:made the sample test fail 
- `sampletest.test.ts` is a unit test. Integration tests are not required because there is no app logic being tested yet.
- Tests are in `tests/frontend/`.
- Regression: because this PR edited the backend job too, I checked the backend job still passes: [Backend CI job #111558211864](https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/37244021821/job/111558211864)