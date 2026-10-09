## Lost In Translation

[Team Contract](docs/contract/499_team7_contract.pdf)

A web-based language learning scavenger hunt game that combines language listening comprehension and physical navigation.

## Overview

(Game name) is designed for beginner language learners to practice recognizing numbers and simple location-based instructions in a real-world environment.

Players listen to audio instructions, navigate to locations, and verify their answers using GPS and image recognition.

The game supports:

- Chinese
- French
- German
- Japanese
- Korean
- Spanish

Players can also select from multiple difficulty levels.

## Features

- Student and teacher accounts
- AI Chatbot that provides language-specific tips
- Language and difficulty selection
- Audio-based location challenges
- GPS-based location verification
- Image recognition for room and office numbers
- Timed game sessions
- Pause, resume, and reset functionality
- Points, badges, and class leaderboards
- Student progress tracking
- Teacher class dashboards and roster management
- Post-game session summaries and debriefs
- Profile customization and point redemption

## Tech Stack

| Component | Technology |
|---|---|
| Frontend | React, TypeScript |
| Backend | Python |
| Authentication | Backend-managed email/password authentication (planned) |
| Database | PostgreSQL 17 |
| Frontend Testing | Vitest, React Testing Library |
| Backend Testing | PyTest |

## System Architecture

[View the system architecture diagram](docs/design/system_architecture.png).

The diagram shows the proposed architecture for **Lost In Translation**, hosted on UBC servers. Students, teachers, and administrators access the application through a web browser on mobile or desktop devices over HTTPS.

- **Frontend (React + TypeScript):** Provides authentication screens, the game interface with maps, audio, and camera access, teacher and administrator dashboards, profiles, rewards, progress views, and the chatbot interface.
- **Backend (Python):** Receives requests through an HTTPS REST API and handles authorization, game sessions, GPS validation, room-number recognition, audio, chatbot integration, class management, and points and rewards. The diagram specifies JWT and role-based access; Firebase Authentication is the authentication provider listed in the tech stack.
- **Data layer:** Uses PostgreSQL for users, classes, game sessions, progress, locations, and rewards. File storage holds audio, images, and uploaded photos, while backup storage supports recovery and log archives.
- **External services:** Provide maps and geolocation, OCR for room numbers, AI-generated learning tips and quiz questions, and account emails and notifications.

The frontend sends game actions and user input to the backend, which coordinates data storage and external services and returns results to the interface. This diagram describes the intended system; hosting, storage, and service integrations are planned components rather than confirmation of the current deployment.
Lost In Translation! uses a **React/TypeScript frontend** to provide the interactive game interface and a **Python backend** to handle application logic and services.

The **Python backend** will manage authentication, while **PostgreSQL** stores application data.
The initial schema includes student, teacher and administrator accounts with a required `password`
field for an encoded password hash, languages, classes and enrollments. Signup/login and password
hashing are separate backend work. See [database setup and design](docs/design/database.md)
for migrations and integration tests.
The **Python backend** will manage authentication, while **PostgreSQL** stores structured application data such as users, classes, game progress, points, and leaderboard information. Every account type (student, teacher, and administrator) will have a required `password` field storing a password hash. Authentication endpoints and account tables are added in subsequent PRs.

## Run the Backend and PostgreSQL Locally

Install Python 3.13 and Docker Desktop, and start Docker Desktop. From the repository root:

```sh
cp .env.example .env
docker compose up -d --wait db
python3 -m venv .venv
source .venv/bin/activate
pip install -r src/backend/requirements.txt
uvicorn main:app --app-dir src/backend --reload
```

Visit `http://localhost:8000/docs` for the API docs. `GET /api/health/db` checks the database connection.
This setup starts PostgreSQL and connects the backend. Application tables and migrations are added separately.

Database connection settings are in `.env` (ignored by Git). When changing the database port or credentials,
update `DATABASE_URL` to match. Docker keeps data in a named volume;
`docker compose stop` stops the database without deleting data. On an existing volume, changing
`POSTGRES_PASSWORD` in `.env` does not change the database password.

Open a PostgreSQL shell:

```sh
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

Run the backend API tests:

```sh
python -m pytest tests/backend -q
```

CI starts a disposable PostgreSQL database for the backend job and tests a real connection through
the health route. Locally, that integration test runs when `DATABASE_URL` is configured; otherwise
it is skipped. The other health-route tests simulate missing configuration and connection failures.
No tests require application tables.

The next PR, **Adding the database schema**, is outlined in
[the schema plan](docs/design/database-schema-plan.md). Keep each PR below 500 total added and
deleted lines, measured against its target branch, including documentation and tests.
Our Data Flow Diagrams (DFDs) document how data moves through the system and how the different components interact with each other.

### Level 0 DFD

The Level 0 DFD provides a high-level overview of the system. It shows the system as a single process and focuses on the main external entities that interact with it and the data exchanged between them.

[View the Level 0 DFD](./docs/design/DFDs/dfd-level0.png)

### Level 1 DFD

The Level 1 DFD provides a more detailed view of the system by breaking the main system process into its major functional areas. To keep the diagram readable, the Level 1 DFD is divided into separate diagrams based on the main areas of functionality:

- **Authentication**: User authentication and account-related data flows. [Authentication DFD](./docs/design/DFDs/auth-dfd.png)
- **Class**: Data flows related to classes and class management. [Class DFD](./docs/design/DFDs/class-dfd.png)
- **Game**: Data flows related to game functionality.  [Game DFD](./docs/design/DFDs/game-dfd.png)
- **Levels**: Data flows related to levels and level progression.  [Levels DFD](./docs/design/DFDs/levels-dfd.png)
- **User**: Data flows related to user information and user-related functionality.  [User DFD](./docs/design/DFDs/user-dfd.png)

The main DFD: [DFD](./docs/design/DFDs/main-dfd-level1.png)
The Level 1 DFD is broken into these smaller diagrams for readability while maintaining consistency with the overall system design.

## User Roles

### Teacher signup API

`POST /api/auth/teacher/signup` accepts `email`, `username`, `password`, `first_name`, and `last_name`.
Passwords require 8+ characters and at most 72 UTF-8 bytes; names/usernames cannot be blank.
Allowlist the lowercase email in `authorized_teacher_emails` first; success returns 201 with `id` and `role: "teacher"`, saving both records atomically.
Errors: 403 `"Error, unauthorized account"`, 409 duplicate identity, 422 invalid input, 503 database failure.
Signup does not verify email ownership, issue a session, or grant class access.

To test locally, start PostgreSQL, install backend dependencies, and export `TEST_DATABASE_URL` with your credentials/port (5433 for the local override).
Run `python -m pytest tests/backend/test_teacher_signup.py -v`.
Integration tests create/migrate/drop a temporary schema (requires schema creation permission); they skip without the URL.
For manual testing, run `python src/backend/migrate.py`, allowlist an email, and submit signup at `http://localhost:8000/docs`.

### Current user API

`GET /api/auth/me` reads the `session` cookie and returns 200 with `email`, `first_name`, `role`, and `redirect_to`; it does not return the password hash.
A missing, expired, or logged-out session returns 401 `"Unauthorized"`; 503 if the database is down.
Protected routes reuse the same check with `Depends(current_user)` from `auth.py`.

### Students

Students can:

- Select a language and difficulty
- Participate in scavenger-hunt sessions
- Complete location-based challenges
- Earn points and achievements
- View their progress and class leaderboard standing

### Teachers

Teachers can:

- Create and manage classes
- Manage student enrollment
- Monitor student progress
- View class-level performance

### Administrators

Administrators manage user accounts and support system maintenance.

## Running the frontend with Docker

Install Docker Desktop and start it, then run from the repository root:

```bash
docker compose up --build
```

Open http://localhost:5173. The React/TypeScript frontend uses Vite, and
edits in `src/frontend/src` reload in the browser automatically.
Stop the containers with `Ctrl+C`, or run `docker compose down`.

After changing frontend dependencies, run `docker compose run --rm frontend npm ci`
to update the dependency volume, then rebuild with `docker compose up --build`.

To run locally without Docker (Node.js 22.12+):

```bash
cd src/frontend
npm ci
npm run dev
```

To serve the production build with Nginx:

```bash
docker build --target production -t lost-in-translation-frontend src/frontend
docker run --rm -p 8080:80 lost-in-translation-frontend
```

Open http://localhost:8080.

### Backend with Docker Compose

`docker compose up --build` starts both the frontend and FastAPI backend as
separate containers. Compose waits for the backend health check before starting
the frontend. Open http://localhost:5173 to see `Backend says: Hello World`.
Vite forwards `/api/` requests to `http://backend:8000` on the Compose network.
The backend is also available at http://localhost:8000/api/hello, with API docs
at http://localhost:8000/docs. Stop both services with `docker compose down`.

If an older standalone backend container is using port 8000, stop it first
with `docker stop capstone-backend`.

This connection applies to the development Compose setup. The standalone
production Nginx image still needs an `/api/` proxy configured in
`src/frontend/nginx.conf` to connect to a backend.

## Testing

The project uses:

- **Vitest** and **React Testing Library** for frontend components and behaviour
- **PyTest** for backend functionality

Testing focuses on:

- Core gameplay
- Authentication
- Data handling
- User interactions

## Project Goals

Lost In Translation! aims to make language practice more interactive, contextual, and engaging by moving listening and vocabulary exercises beyond traditional screen-based quizzes.

## Team

**Team 7**
- Gamuchirai Mhere
- Madiba Burks Magara
- Ashish Nayak
- Dan Rukundo
