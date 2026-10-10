# Week 5 Team Log: Team 7

Authors: Ashish, Dan, Gamu, Madiba

## PRs covered

| PR | Author | What | Status |
|---|---|---|---|
| [#43](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/43) | Gamu (gamurrrrr) | Shared password hashing and verification | Merged |
| [#44](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/44) | Ashish (nayakashish) | User login endpoint | Merged |
| [#45](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/45) | Dan (danruk) | Authorized teacher signup endpoint | Merged |
| [#47](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/47) | Ashish (nayakashish) | Logout endpoint | Merged |
| [#49](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/49) | Gamu (gamurrrrr) | Admin endpoint to reassign a class to an approved teacher | Merged |
| [#51](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/51) | Ashish (nayakashish) | Repository PR template | Merged |
| [#52](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/52) | Gamu (gamurrrrr) | Seed script for the initial admin account | Merged |
| [#56](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/56) | Dan (danruk) | Teacher class access | Merged |
| [#57](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/57) | Ashish (nayakashish) | Current-user endpoint | Merged |
| [#58](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/58) | Dan (danruk) | Admin approval of teacher signup emails | Merged |
| [#61](https://github.com/COSC-499-W2026/capstone-project-team-7/pull/61) | Madiba (KoesOremus) | Student registration service | Merged |

## Goal and work distribution

- Following last week's stack setup, our goal was to begin the account and authentication features and connect them to PostgreSQL.
- Ashish implemented login, logout, and current-user lookup (#44, #47, #57), and added a PR template (#51).
- Dan implemented authorized teacher signup, teacher class access, and admin approval of teacher emails (#45, #56, #58).
- Gamu implemented shared password hashing, class reassignment, and the initial admin seed script (#43, #49, #52).
- Madiba implemented the student registration service (#61).
- The merged work establishes the backend pieces for student registration, an administrator to approve teacher emails, authorized teachers to create accounts, users to log in and out, and authenticated requests to identify the current user. Teacher class access and admin class reassignment extend this foundation into class authorization.

## Code-base health

- **Shared authentication rules.** Signup and admin seeding reuse the bcrypt password helper. Teacher signup enforces the 72-byte bcrypt limit before hashing and creates user and teacher records in one transaction, preventing partial accounts.
- **Authorization across features.** Teacher approval and class reassignment require an admin session. Teacher signup checks the approved email list. These checks connect account creation to the role restrictions needed by class features.
- **Overlapping edits.** Router registrations in `main.py` and API documentation in `README.md` caused merge conflicts. The resolutions need to preserve both features: the teacher approval and admin routers, and the teacher approval and current-user documentation sections. Future branches should start from the latest `dev`, with shared-file edits coordinated during review.
- **Local database compatibility.** Dan's individual log records a PostgreSQL 18 data volume conflicting with the project's PostgreSQL 17 configuration. Teacher signup was checked using a separate temporary PostgreSQL 17 database; repair of that local setup remains outstanding.

## Testing and validation

- The supplied PR lists show successful checks for the ten merged backend PRs, including 2/2 checks for student registration (#61). The PR template change (#51) is shown as approved and merged without a checks count. Detailed student registration test cases are not visible in the screenshots.
- Dan's signup log records nine passing automated cases for invalid input and database failure, plus separate PostgreSQL checks for successful signup, unauthorized signup, duplicate signup, and transaction rollback. The retained automated signup tests do not verify successful persistence.
- Gamu's log documents password hashing tests for correct and incorrect passwords, hashes differing from plaintext, and random salts producing different hashes for the same password.
- Gamu's class reassignment tests cover approved teachers, rejected unapproved teachers, and admin authorization. The documented database integration test also checks that student enrollment survives reassignment.
- The admin seed tests cover creating an account that can log in, avoiding duplicate initial admins, and rejecting passwords over the bcrypt limit. Database-dependent tests require the relevant database environment variable and may skip when it is absent; passing CI alone does not establish that all integration cases ran.

## Architecture and DFD alignment

This week's work implements the backend authentication approach agreed last week after removing Firebase. FastAPI handles account and session requests, PostgreSQL stores account and authorization data, and the shared bcrypt helper handles password hashing and verification.

The initial admin is created through a setup script rather than a public signup endpoint. That account can use the admin-only approval and class reassignment features. Class reassignment changes the class's teacher reference while preserving student enrollment. Teacher signup establishes an account; class access is handled separately.

We updated our system architecture to reflect these authentication and administration changes and merged the updated architecture into `dev`.

## Collaboration process and next steps

The team continued using PR review for feature integration and added a shared PR template (#51). The supplied lists mark all eleven merged PRs as approved. Merge conflicts in shared files highlight the need to check that all router imports, registrations, and documentation survive integration.

Next steps are to connect the account flows to frontend pages and verify student registration alongside the combined teacher approval, signup, login, current-user, class-access, and logout flows against PostgreSQL. Individual logs should also be updated with final PR links and specific reviewer feedback where those details are still missing.
