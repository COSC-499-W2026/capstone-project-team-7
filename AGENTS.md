# AGENTS.md

Instructions for AI coding assistants (Claude, Codex, ChatGPT) and team members working in this repo.

## Project

Lost In Translation. A web-based scavenger hunt game for beginner language students at UBCO.

- Languages: Chinese, French, German, Japanese, Korean, Spanish. Teachers choose the language.
- Students hear audio clues (numbers and/or descriptions), walk to rooms on campus, and confirm with GPS and a photo of the room number.
- Levels: Basic (numbers only), Advanced (numbers and descriptions), Expert (descriptions only).
- Each session picks 5 random locations from a pool of 15-20.
- Game sessions support pause, resume, reset, and shuffle.
- Points, badges, and leaderboards for students. Dashboard for teachers. Admin accounts for account management.
- Requirements and test cases: `docs/Proposal/499 - Team 7 Project Proposal.md` on `dev`.

## Stack

| Area | Technology |
|---|---|
| Frontend | React, TypeScript, Vite (`src/frontend`) |
| Backend | Python, FastAPI (`src/backend`) |
| Database | PostgreSQL 17, SQL migrations (`src/backend/migrations`) |
| Auth | Backend-managed. bcrypt password hashes. Cookie sessions in the `sessions` table. |
| Tests | Pytest (`tests/backend`), Vitest (`tests/frontend`) |
| CI | GitHub Actions (`.github/workflows/ci.yml`) |

`dev` is the most up-to-date branch. Read it before assuming something does not exist.

## Code rules

### Structure

- No god files. One module per feature area. Example: `auth.py` for login and logout.
- One purpose per function. If a function needs "and" to describe it, split it.
- Keep route handlers thin. Put reusable logic in `src/backend/utils/` or a feature module.
- Frontend: one component per file.

### Reuse before writing

Search the codebase first. Do not recreate what exists.
If you need the same logic in two places, move it to one shared place.

### Comments and docs

- Do not over-comment. Code should explain what it does.
- Comment only the non-obvious why. One line where possible.
- Describe endpoints with a short docstring or `summary=`. FastAPI shows these in `/docs`.
- Describe request fields with Pydantic `Field(description=...)` where the name is not clear.
- Update `README.md` or `docs/` when behaviour changes.

### API

- Prefix routes with `/api`. Group by feature with `APIRouter(prefix=...)`.
- Validate input with Pydantic models.
- Return correct status codes: 201 created, 401 not logged in, 403 not allowed, 404 not found, 409 conflict, 422 bad input, 503 database unavailable.
- Error messages must be user friendly. Do not leak internal details, stack traces, or whether an email exists.

### Database

- Every schema change is a new numbered migration: `003_<name>.sql`.
- Never edit a migration that has been merged. `migrate.py` rejects changed files.
- Use parameterized queries (`%s`). Never build SQL with string formatting.

### Security

- Never commit secrets or `.env`. Use `.env.example` for new settings.
- Never store or log plain passwords or session tokens.
- Check the user's session and role on every protected route.

## Testing

- Every requirement needs a positive and a negative test.
- Unit tests: fake the database with `monkeypatch`. See `FakeConnection` in `tests/backend/test_auth.py`.
- Integration tests: run against Postgres.
- Test error paths: bad input, missing auth, database failure.
- Do not mark work done until tests pass.

Commands:

```sh
python -m pytest tests/backend
cd src/frontend && npm test
```

## Rules for AI assistants

- Follow the existing style of the file you edit.
- Make the smallest change that meets the issue. No unrequested features or refactors.
- Do not add dependencies without asking.
- Do not commit, push, or open PRs unless told to.
- Run the tests. Report failures as they are. Do not claim something works without running it.
- Ask when a requirement is unclear. Do not guess.
