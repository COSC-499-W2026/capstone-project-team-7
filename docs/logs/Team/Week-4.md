# Week 1 Team Log: Team 7

Authors: Ashish, Dan, Gamu, Madiba


## PRs covered

| PR | Author | What | Status | Reviewed by |
|---|---|---|---|---|
| #6 | Ashish (nayakashish) | FastAPI backend skeleton + 2 PyTest tests (`/api/hello`), issue #2 | Merged (into `main`) | Gamu, Dan |
| #8 | Gamu (gamurrrrr) | Backend CI workflow (`ci.yml`) | Merged | Ashish, Dan |
| #11 | Dan (danruk) | Docker setup, issue #3 | Merged | Ashish |
| #14 | Dan (danruk) | Revert of #11 (merged by mistake) | Merged | None |
| #13 | Ashish (nayakashish) | React frontend skeleton calling `/api/hello`, issue #7 | Merged | Gamu, Dan |
| #17 | Dan (danruk) | Frontend Docker, issue #16 | Merged | Gamu, Ashish |
| #18 | Madiba (KoesOremus) | PostgreSQL 17 setup, migrations, health check, Docker Compose, integration tests | merged | Gamu, Dan |
| #19 | Gamu (gamurrrrr) | Frontend CI job, Vitest config + placeholder test, removed report-saving step | merged | Ashish, Dan |

---

## Goal and work distribution

- This week, we decided to focus on project setup with the goal of having a runnable skeleton of the stack from our proposal (FastAPI backend, React frontend, PostgreSQL, Docker) and automated testing in CI, so feature work can start in week 5.
- The work was distributed so that Ashish focused on the FastAPI and React skeletons (#6, #13), Dan focused on Docker (#11/#14, #17), Madiba focused on the PostgreSQL setup (#18), and Gamu focused on CI for the backend and frontend (#8, #19). Everyone reviewed at least one other person's PR.
- We did not consider alternative workload distributions because everyone chose the tasks they wanted to tackle.
- Based on the merged PRs (#6, #8, #13, #17 and #19) and the passing CI runs for both the backend and frontend, we met this goal because the FastAPI and React skeletons are in `dev`, each has automated tests running on every push and PR, and the frontend runs in Docker.Our databse is also configured within Docker. Our plan for next week is to add the backend to the Docker setup. 

## Code-base health

By cross-reading each other's PRs and running code on our local machines, we found these problems:

- **Changes in one component require changes elsewhere.** The decision to stop using Firebase for authentication affects the database schema, system diagrams, and the README. 
- **Overlapping edits to the same files.** Dan's Docker branch was built on top of Ashish's earlier React commits and edited some of the same React files, which caused merge conflicts on #13. Ashish resolved them, and the frontend now includes the call to the backend. To reduce this, we agreed to branch from the latest `dev` and tell each other before touching shared files.
- **PR size.** Most of our PRs this week are an appropriate size. The ones that look large are inflated by auto-generated files: `package-lock.json` (and `package.json` changes from installing dependencies) account for most of the lines in #13 and #19. For example, about 288 of the 318 changed lines in #19 are the lock file. The hand-written changes in those PRs are small.

## Things Changed in DFD and Architecture Diagram
After discussing internally and with Dr. Hui, we have removed firebase auth from the scope and the diagrams. Rather than relying on another external system, we will implement this ourselves. This makes the system more consolidated and less reliant on multiple systems. 
With this change, our database structure has been modified as well as we now collect user information such as emails and passwords. The password information will be hashed in our database.


## Collaboration process
We changed our collaboration process so that `dev` is protected, so changes need a PR and two reviewers before merging. 

In our last weekly meeting we had agreed that by this sprint end we would have a functioning framework to begin building the main app and features in. Based on our our progress and contributions, we have met this goal of having a minimal working framework. With this template built, we will begin adding app specific features and pages.

This week we will introduce creating accounts, logging in and out, and building the api between the database and the app.