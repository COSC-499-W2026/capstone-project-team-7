### Week 5: Ashish Nayak
Oct 4 to Oct 11

**Contents**

1. [Summary](#1-summary)
2. [PR #44: Login](#2-pr-44-login)
3. [PR #47: Logout](#3-pr-47-logout)
4. [PR #57: Current user](#4-pr-57-current-user)
5. [Non Code PRs](#5-non-code-prs)
6. [Reviews I gave](#6-reviews-i-gave)
7. [How this fits the overall system](#7-how-this-fits-the-overall-system)

---

## 1. Summary

Merged this week: 3 code PRs on `dev` (#44, #47, #57), 1 docs PR on `dev` (#62) and 1 process PR on `main` (#51).

| PR | Issue | Requirement | Size | Reviewers |
|---|---|---|---|---|
| #44 Login | #33 | Users with accounts can log in | 4 files, +214 | Gamu, Dan |
| #47 Logout | #37 | Users can log out | 2 files, +76/−3 | Gamu (changes requested, then approved), Dan |
| #57 Current user | #48 | Report whether the current user is logged in | 3 files, +134/−4 | Gamu, Dan |

PRs 44, 47, 48 are my merged code prs this week. 
I also merged PR 51 which adds a pr template to the repo. And 62 which merges the docs branch into dev so that dev has updated documentation. 


**Claim labels.** *Observed* means I ran it or saw it (test output, CI result, review text). *Generated* means AI-written code that I reviewed. "Re-run" test counts come from running `python -m pytest tests/backend` at each merge commit on Oct 10 against my local PostgreSQL. The CI backend job passed on the final commit of #44, #47 and #57 (observed).

---

## 2. PR #44: Login

Endpoint: `POST /api/auth/login`

- [x] As part of the requirement "the system shall allow users with accounts to log in" (#33), a student, teacher or admin needs to enter an email and password, be authenticated, and be sent to their role's dashboard. Therefore, I implemented login() in auth.py and a sessions table. All three user groups can start a 7-day cookie session, and the response gives their dashboard.
- [x] When I reviewed login(), AI flagged to me that bcrypt only uses the first 72 bytes of a password, so a longer password sharing those 72 bytes would also be accepted. Gamu also raised this in her review. Therefore, I added a MAX_PASSWORD_BYTES variable and reject longer passwords with the same invalid credentials error. Limitation: signup must enforce the same limit.
- [x] When I reviewed the error paths, I made unknown email and wrong password return the same 401 invalid credentials. Different messages would let anyone check which emails have accounts.
- [x] The PR does not contain any temporary workaround because the session design is the long-term authentication model. Logout (#47) and the current-user check (#57) built on it without changes.
- [x] The PR contains one route function, login(), of about 30 lines.
- [x] I kept constants named and reused Gamu's verify_password() instead of calling bcrypt directly, and used one try block with a single 503 path. I can confirm the contribution does not contain any of the following:
  - hardcoded values
  - duplicate code
  - dead code
  - unnecessary function calls
  - excessive conditional logic
  - deep nesting
  - high cyclomatic complexity
  - classes/modules/functions with many unrelated responsibilities
- [x] Dan approved with no changes. Gamu's review identified the bcrypt length issue, which I fixed.
- [x] This work is written in the new auth.py file because login, logout and session checks are one feature area, and the team rule is one module per feature area.
- [x] This work belongs in processes 1.2 Login Existing Account and 1.3 Verify Account of the Authenticate User DFD (Level 2). It receives credentials, checks them against D1 User Data, and returns the role used by 1.6 Route by Role.

**Data receipts**

- [x] Session data is modeled as a sessions table row, because logout must be able to revoke a session immediately. I considered stateless signed tokens (JWT), but a JWT stays valid until it expires unless a revocation list is added, and that list is a sessions table anyway.
- [x] Login input is validated by the Pydantic model LoginRequest (email and password required, otherwise 422), plus the 72-byte password limit.
- [x] The session token could be stolen if the database leaked. Therefore, only its SHA-256 hash is stored, and the raw token exists only in the user's cookie (the test asserts the stored value equals `sha256(cookie)`). This is one-way hashing, not encryption. I considered bcrypt for tokens, but a 32-byte random token cannot be brute-forced, and every authenticated request looks the token up, so a fast hash is needed.

**Tests (same PR)**

- [x] Happy path: `test_correct_password_creates_session_and_returns_dashboard` (student, teacher, admin) and `test_login_against_database` (real user, correct password, 200, one session row stored as a hash) passed.
- [x] Abnormal: `test_missing_fields_are_rejected` (3 bodies, 422), `test_database_unavailable_returns_503` (missing `DATABASE_URL`, connection failure) and `test_password_over_bcrypt_limit_is_rejected` passed.
- [x] Negative: `test_wrong_password_is_rejected_without_session` and `test_unknown_email_gets_same_error_as_wrong_password` returned 401 with no session and no cookie, as expected.
- [x] All are unit tests with a fake connection (`FakeConnection` via `monkeypatch`), except `test_login_against_database`, which is an integration test against PostgreSQL. It is needed because the fake cannot verify the SQL, the case-insensitive email lookup, or the stored hash.
- [x] Directory: `tests/backend/test_auth.py`.
- [x] This PR did not break anything else in the system: CI passed, and a re-run at merge commit `d2ba12d` gives **41 passed** (auth: 12).
- [x] I also manually ran tests on my code using the local docker psql interface as well as testing the api through the swagger docs/ page. From there I could modify parameters and test our happy paths and negative paths. All my tests passed.

---

## 3. PR #47: Logout

Endpoint: `POST /api/auth/logout`

- [x] As part of the requirement "the system shall allow users to log out" (#37), a logged-in user needs to end their session so the token cannot be reused. Therefore, I implemented logout() in auth.py. It deletes the session row matching the cookie's hash and clears the cookie, for all roles.
- [x] When I reviewed logout(), I did not find a problem with the core logic. A single sql command both invalidates the token and reports whether it was valid.
- [x] The PR does not contain any temporary workaround because it reuses #44's session model and cookie settings unchanged.
- [x] The PR contains one function, logout(), of about 18 lines.
- [x] I reused SESSION_COOKIE and the same 503 pattern as login(), and return one 401 Unauthorized for no cookie, unknown token and expired session, with no branch per case. I can confirm the contribution does not contain any of the following:
  - hardcoded values
  - duplicate code
  - dead code
  - unnecessary function calls
  - excessive conditional logic
  - deep nesting
  - high cyclomatic complexity
  - classes/modules/functions with many unrelated responsibilities
- [x] Gamu's review identified that though the code had the following: "no cookie gives 401" and "database down gives 503", neither was tested. Therefore, I added two tests to ensure these edge cases worked as intended. Gamu then approved, and Dan approved.
- [x] This work is written in auth.py`because it is the inverse of login and shares its constants.
- [x] This work belongs in the Authenticate User process (1.0) in the DFD.

**Tests (same PR)**

- [x] Happy path: `test_logout_deletes_session_and_clears_cookie` and the extended `test_login_against_database` passed.
- [x] Abnormal: `test_logout_database_unavailable_returns_503` passed.
- [x] Negative: these returned **401** as expected:
  - `test_logout_with_invalidated_token_is_unauthorized`
  - `test_logout_without_cookie_is_unauthorized` (also checks that nothing was deleted)
- [x] Unit: the four `test_logout_*` tests. Integration: `test_login_against_database`.
- [x] Directory: `tests/backend/test_auth.py`.
- [x] This PR did not break anything else in the system: CI passed, and a re-run at merge commit gives 45 passed.

---

## 4. PR #57: Current user

Adds the `current_user` dependency and `GET /api/auth/me`.

- [x] As part of the requirement "the system shall report whether the current user is logged in" (#48), a client needs one endpoint that returns who is logged in (200) or that nobody is (401), and every protected route needs the same check. Therefore, I implemented:
  - current_user(): a reusable FastAPI dependency that looks up the session cookie, finds an unexpired session joined to the user, and otherwise returns 401
  - GET /api/auth/me: returns emai;, first_name, role and redirect_to for all roles
- [x] I had AI review the code and it found these problems:
  - Duplicate code: sha256(token.encode()).hexdigest() would have appeared three times (login, logout, current user). So I refactored into hash_token(), which gets reused everywhere, and re-ran the login and logout tests to confirm their behaviour was unchanged.
- [x] The PR does not contain any temporary workaround because current_user is the long-term shared session check. Observed: Gamu's admin reassign PR (#49) uses it (require_admin depends on current_user) instead of writing its own check. Dan's branch reimplements it, however I have verified with him that he will be refactoring his code to use the current_user dependency. 
- [x] The PR contains small functions: hash_token (2 lines), current_user (about 22 lines) and me (7 lines).
- [x] I can confirm the contribution does not contain any of the following:
  - hardcoded values
  - duplicate code within `auth.py`
  - dead code
  - unnecessary function calls
  - excessive conditional logic
  - deep nesting
  - high cyclomatic complexity
  - classes/modules/functions with many unrelated responsibilities

  Limitation: as mentioned above two teammates' modules still contain their own session checks, written before `current_user` existed. A refactor issue was requested in those reviews.
- [x] Gamu's review asked me to resolve merge conflicts, which I did afterwards. Dan then approved and I merged.
- [x] This work is written in auth.py because the dependency and /me read the same sessions and users data as login and logout.
- [x] This work belongs in 1.3 Verify Account and 1.6 Route by Role in the DFD, because /me verifies the session against D1 and returns redirect_to for the role's dashboard.

**Data receipts**

- [x] Access control: /me lets a user read only their own profile fields, and only with a valid, unexpired session. Other routes will restrict access by adding Depends(current_user), with a role check on top where needed.
- [x] Privacy: missing, unknown, expired and logged-out tokens all get the same 401 Unauthorized, so a caller cannot tell whether a token ever existed. /me excludes the password hash and the user id.

**Tests**

- [x] Happy path: `test_me_with_valid_session_returns_user` (3 roles) passed. Its fake row includes a bcrypt hash, and the test asserts the hash is not in the response. `test_me_against_database` (real login, then `/me` returns 200 with the exact body) also passed.
- [x] Abnormal: `test_me_database_unavailable_returns_503` passed.
- [x] Negative: these returned **401** as expected:
  - no cookie: `test_me_without_cookie_is_unauthorized`, which also asserts the database is never opened
  - unknown or expired token: `test_me_with_unknown_or_expired_session_is_unauthorized`
  - in `test_me_against_database`: a session that expired 1 second ago, and the same token reused after logout
- [x] Unit: the four `test_me_*` tests other than `test_me_against_database`. Integration: `test_me_against_database`.
- [x] Directory: `tests/backend/test_auth.py`.
- [x] This PR did not break anything else in the system: CI passed, and a re-run at the merge commit gives **77 passed**. I also checked it manually on the Docker stack through `/docs` (observed): login 200, `/me` 200, no cookie 401, logout 200, `/me` with the old token 401.

---

## 5. Non Code PRs:
PR #51: PR template - Process change, no code.
PR #62: Docs update - Documentation only, no code.

---

## 6. Reviews I gave

| PR | Author | What I found | Outcome |
|---|---|---|---|
| #45 Teacher signup | Dan | No happy-path test for a successful signup | Changes requested. Dan added a happy-path integration test, then I approved. |
| #55 Student signup schema | Madiba | Email local part not lowercased, inconsistent with teacher signup; validation could be shared with teacher signup | Changes requested. Lowercase validator and tests added, then I approved. |
| #56 Teacher class access | Dan | Its own session check duplicates current_user | Approved after Dan confirmed he will refactor to use current_user in subsequent PR |
| #58 Approve teacher emails | Dan | Same duplicated auth check | Approved; refactor requested similar to above|
| #52 Seed admin | Gamu | No issues; correctly placed in utils/ | Approved |

## 7. How this fits the overall system

Login, logout and current_user form the backend's authentication layer. Login creates the session, logout ends it, and current_user is the single check that protected routes use. Signup creates the accounts that login authenticates.

With the login backend logic in place, we can begin building up code that will be user specific, such as dashboards, hunts, leaderboards, etc. 