# Week 4 Individual Log: Dan Rukundo

### For PR #17 — Add Docker for the frontend

[PR #17](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/17) — merged into `dev`.

- As part of the Technology Stack and frontend Docker setup requirement (issue #16), the team needs to build and run the frontend consistently. Therefore, I added a frontend Dockerfile, Docker Compose configuration, a minimal React/TypeScript scaffold, and README instructions. Developers can run `docker compose up --build` and access the frontend on port 5173; the production image serves built files with Nginx.
- The PR changed 12 files with 1,452 added lines, but **1,263 lines (about 87%) were dependency metadata in `package-lock.json`**. The remaining 189 added lines were configuration, scaffolding, and documentation. The only named application function, `App()`, was 11 lines long.
- The Docker configuration was checked for the correct build context, ports, source mounts, and dependency installation. The PR's validation records show that the frontend build, Compose configuration, and development and production image builds passed.
- The initial page is a scaffold. Production `/api/` requests currently return 503 until a backend proxy is added, so production backend integration remains incomplete.
- The clean code check covered duplication, dead code, unnecessary calls, excessive conditions, deep nesting, complexity, and unrelated responsibilities. The scaffold has no branches or loops, and each configuration file has one role. Ports and base images are explicit defaults, while `API_PROXY_TARGET` can be overridden.
- Ashish and Gamu approved the PR. The supplied screenshot does not show any requested corrections.
- `compose.yaml` belongs at the repository root to orchestrate services, while the frontend Dockerfile and Nginx configuration belong under `src/frontend`. This supports deployment of the Frontend UI process in the DFD; Docker configuration itself is outside the runtime data flow. No database or user-data validation changes were made.

For Tests:

- No new automated tests were written. The frontend build, Compose validation, and both image builds passed, as recorded in the PR description.
- These checks validate packaging; they do not establish complete frontend/backend integration. No negative-case or abnormal-situation tests were recorded for this PR.
- The PR description contains the validation summary. A build-output screenshot or report still needs to be added for the rubric's evidence requirement.

---

### For PR #21 — Add backend Docker

[PR #21](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/21) — awaiting approval in the supplied screenshot; not yet confirmed merged.

- As part of the backend Docker setup requirement (issue #20), the team needs to build an image and run the existing FastAPI backend. Therefore, I added `src/backend/Dockerfile`, which installs the backend dependencies and starts Uvicorn on `0.0.0.0:8000`. This PR adds seven lines and no application functions, database changes, or user-data validation.
- The Dockerfile was checked against `main.py` and `requirements.txt`. The image built successfully, the container started, and a live request to `/api/hello` inside the container returned HTTP 200 with `{"message": "Hello World"}`.
- The Dockerfile packages the current backend without a workaround for application logic. It copies only `main.py`, so it will need updating when the backend uses additional modules.
- The clean code check found no duplicated application code or unnecessary instructions. Each instruction prepares or starts the backend; no conditional logic, nesting, or complex functions were added. Python 3.12 and port 8000 are runtime defaults, and no credentials are embedded.
- Gamu approved the PR; other approvals were still pending in the supplied screenshot.
- The Dockerfile belongs beside the backend source and dependencies because they form its build context. This supports deployment of the Backend API process in the DFD; the Dockerfile itself is outside the runtime data flow.

For Tests:

- No new tests were written. Both existing API tests in `tests/backend/test_main.py` passed inside the Docker image.
- `test_hello_returns_message` checks HTTP 200 and the exact JSON response. `test_unknown_route_returns_404` checks that an unknown endpoint returns HTTP 404; the rejection was expected and the test passed.
- These are API integration tests using FastAPI's `TestClient`. The separate live request also checked that the containerized server responds. PostgreSQL and frontend/backend connectivity were not tested.
- The existing backend suite passed with **2 passed**, providing a regression check for the current API. A test-output screenshot or CI report still needs to be added as proof.

---

## How this fits the overall system

These PRs provide Docker packaging for the React/TypeScript frontend and Python FastAPI backend. They help teammates run the chosen stack consistently and prepare the services for later integration, including PostgreSQL.
