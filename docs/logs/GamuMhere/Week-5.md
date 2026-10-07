# Week 5 Individual Log: Gamu

Team 7 | Repo: capstone-project-team-7 | PRs this week: #43 (password hashing) merged into dev; # () merged into dev

---

## PR #43: Secure password hashing (branch `35-encrypting-user-passwords`, into `dev`)

**Size:** 4 files changed, +35 / -1 lines (`src/backend/utils/passwords.py` added, `tests/backend/test_hash_passwords.py` added, `src/backend/requirements.txt` updated).

- As part of the account/authentication requirement (task #35), passwords must never be stored as plain text in our PostgreSQL database. Since the team dropped Firebase, our own signup, login and password change code needs a safe way to hash and check passwords.
- Therefore, I implemented `hash_password(password)` in `src/backend/utils/passwords.py`, which turns a plain password into a bcrypt hash with a random salt, and `verify_password(password, hashed_password)`, which checks a typed password against a stored hash and returns True or False. I also added `bcrypt` to `requirements.txt` so CI and teammates install it.

**Review receipts**

- When I reviewed my first version, I placed `passwords.py` in `src/utils/`, but `pytest.ini` has `pythonpath = src/backend`, so the tests could not import it. Therefore, I moved it to `src/backend/utils/`, which is still inside `src/` and avoids editing the shared `pytest.ini`.
- When I reviewed `hash_password`, I noticed bcrypt only reads the first 72 bytes of a password. I did not add a length check here because password rules belong to signup (#32) and password change (#34), so I am flagging it to those owners instead of editing their code.
- Hashing, not encryption, was chosen on purpose: a hash cannot be turned back into the original password, so a leaked database does not expose real passwords.
- The PR contains two functions, each under 10 lines, and no workarounds or temporary code.
- [Add feedback from your reviewer and what you changed. Add any PRs you reviewed for teammates, with the PR number and what you found.]

**Architecture receipts**

- `passwords.py` is in `src/backend/utils/` because the PR rules say utility files go under `src/`, and `pytest.ini` points Python at `src/backend`, so the same import style as `main.py` works. The test is in `tests/backend/` as required.
- In the DFD, this sits inside the backend authentication process. On signup and password change, the plain password goes through `hash_password` and only the hash is saved in PostgreSQL. On login, `verify_password` compares the typed password with the stored hash. Plain passwords are never written to the database.
- No existing code was edited. Signup (#32), login (#33) and password change (#34) can import these functions directly.

**Clean Code Check**

- I re-read both functions and the tests for hardcoded values, duplicate code, dead code, deep nesting and unrelated responsibilities. Each function does one job, the file is short, and there is no duplicated or dead code.

**Testing receipts**

- Happy path: `test_verify_password_correct` hashes a password and confirms `verify_password` returns True for the same password.
- Negative case: `test_verify_password_incorrect` confirms `verify_password` returns False for a wrong password.
- Extra checks: `test_hash_is_not_plaintext` confirms the stored value is not the real password, and `test_same_password_hashes_differ` confirms the random salt works.
- These are unit tests. Integration tests are not required yet because the users table and the signup/login endpoints belong to other PRs.
- Tests are in `tests/backend/test_hash_passwords.py`.
- Regression: no existing files were changed apart from adding one line to `requirements.txt`. Backend CI run: (CI Run)[https://github.com/COSC-499-W2026/capstone-project-team-7/actions/runs/37566144985/job/112614196375?pr=43]