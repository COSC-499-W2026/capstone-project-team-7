## Lost In Translation!

[Team Contract](docs/contract/499_team7_contract.pdf)

A web-based language learning scavenger hunt game that combines language listening comprehension and physical navigation.

## Project Goals

Lost In Translation! aims to make language practice more interactive, contextual, and engaging by moving listening and vocabulary exercises beyond traditional screen-based quizzes.

## Overview

Lost In Translation! is designed for beginner language learners to practice recognizing numbers and simple location-based instructions in a real-world environment.

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

The diagram shows the architecture for **Lost In Translation**, hosted on UBC servers. Students, teachers, and administrators access the application through a web browser on mobile or desktop devices over HTTPS.

- **Frontend (React + TypeScript):** Provides authentication screens, the game interface with maps, audio, and camera access, teacher and administrator dashboards, profiles, rewards, leaderboard, and progress views.
- **Backend (Python + FastAPI):** Provides a REST API and handles authentication, game sessions, GPS validation, room-number recognition, audio, class and account management, points, badges, rewards, debrief, and progress. Authentication uses session cookies, with sessions and bcrypt password hashes stored in PostgreSQL and role checks on protected routes. Room numbers are read with PaddleOCR, which runs inside the backend.
- **Data layer:** Uses PostgreSQL for users, classes, game sessions, progress, locations, clues, and rewards. Clue audio is stored as files alongside the backend.
- **External services:** Gmail SMTP sends password reset emails.

The frontend sends game actions and user input to the backend, which reads and saves data and returns results to the interface. The diagram shows the intended system, so some parts are still being built. See [database setup and design](docs/design/database.md) for migrations and integration tests.

### Level 0 DFD

The Level 0 DFD provides a high-level overview of the system. It shows the system as a single process and focuses on the main external entities that interact with it and the data exchanged between them.

[View the Level 0 DFD](./docs/design/DFDs/dfd-level0.png)

### Level 1 DFD

The Level 1 DFD breaks the main system process into its major functional areas, and shows the data they exchange with users, external systems, data stores, and each other.

[View the Level 1 DFD](./docs/design/DFDs/main-dfd-level1.png)

### Level 2 DFDs

The larger Level 1 processes are broken down further in their own diagrams:

- **1.0 Authenticate User**: Accounts, login, sessions, and password resets. [Authentication DFD](./docs/design/DFDs/auth-dfd.png)
- **5.0 Play Game**: Starting a game, clues and audio, GPS and photo checks, and points. [Game DFD](./docs/design/DFDs/game-dfd.png)
- **9.0 Class Management**: Classes, rosters, joining by code, and assigned hunts. [Class DFD](./docs/design/DFDs/class-dfd.png)
- **10.0 User Management**: Approving teacher emails and managing accounts and classes. [User DFD](./docs/design/DFDs/user-dfd.png)
- **11.0 Manage Level Content**: Adding locations and audio. [Levels DFD](./docs/design/DFDs/levels-dfd.png)

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


## User Roles

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


## Team

**Team 7**
- Gamuchirai Mhere
- Madiba Burks Magara
- Ashish Nayak
- Dan Rukundo
