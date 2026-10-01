## Lost In Translation

[Team Contract](docs/contract/499_team7_contract.pdf)

A web-based language learning scavenger hunt game that combines language listening comprehension and physical navigation.

## Overview

Lost In Translation is designed for beginner language learners to practice recognizing numbers and simple location-based instructions in a real-world environment.

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
- Points, badges, and leaderboards
- Student progress tracking
- Teacher class dashboards and roster management
- Post-game session summaries and debriefs
- Profile customization and point redemption

## Tech Stack

| Component | Technology |
|---|---|
| Frontend | React, TypeScript |
| Backend | Python, FastAPI |
| Authentication | Firebase Authentication |
| Database | PostgreSQL |
| Local Development | Docker Desktop, Docker Compose |
| Frontend Testing | Vitest, React Testing Library |
| Backend Testing | PyTest |

## Local development with Docker

Install and start Docker Desktop. From the repository root, run:

```bash
cp .env.example .env
docker compose up --build
```

Only copy `.env.example` on first setup; keep your existing `.env` afterward.
The example credentials are for local development only. `.env` is ignored by Git.

Once the services have started, open these links in your browser:

| Service | Local link | Purpose |
|---|---|---|
| React frontend | [http://localhost:5173](http://localhost:5173) | Open the application |
| FastAPI documentation | [http://localhost:8000/docs](http://localhost:8000/docs) | Explore and try API endpoints |
| Health check | [http://localhost:8000/api/health](http://localhost:8000/api/health) | Check the API and database connection |

These links work on the computer running Docker while the services are running.

The starter page shows “Connected and ready.” when the frontend can reach
FastAPI and FastAPI can query PostgreSQL. Firebase authentication and game
features are not implemented in this starter.

Compose runs React/Vite, FastAPI, and PostgreSQL 18. The frontend forwards
`/api` requests to the backend through Vite's development proxy. PostgreSQL is
available to the backend at `db:5432` inside Docker.

Edits under `src/frontend/src` and `src/backend/app` reload automatically.
After changing dependencies, Dockerfiles, or Vite configuration, stop and run
`docker compose up --build` again. Commit `package-lock.json` with frontend
dependency changes. You do not need a local Node or Python installation to run
this setup.

Useful commands, run from the repository root:

```bash
docker compose up                 # Start again after initial setup
docker compose ps                 # Check service status
docker compose logs -f backend    # Follow backend logs
docker compose down              # Stop services; retain database data
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

Keep the terminal running while using the app. To stop, press `Ctrl+C`, then
run `docker compose down` to remove the stopped containers and network.

If a Mac terminal reports `command not found: docker`, reopen the terminal
(or fully quit and reopen VS Code when using its terminal). If needed, add
Docker's command-line tools to the current terminal's PATH:

```bash
export PATH="/Applications/Docker.app/Contents/Resources/bin:$HOME/.docker/bin:/usr/local/bin:$PATH"
docker --version
```

If Docker reports that it cannot connect to the daemon, open Docker Desktop
and wait for its engine to start before retrying.

Database data lives in the `postgres_data` Docker volume and survives normal
stops and rebuilds. `docker compose down -v` deletes that data. PostgreSQL reads
the initial database credentials when creating a fresh volume; changing `.env`
does not update credentials in an existing database.

This configuration is for local development and binds the web ports to your
computer's loopback interface. Production deployment and testing from a phone
will need separate configuration.

## System Architecture

Lost In Translation uses a **React/TypeScript frontend** to provide the interactive game interface and a **Python/FastAPI backend** to handle application logic and services.

The planned authentication service is **Firebase Authentication**, while **PostgreSQL** will store structured application data such as users, classes, game progress, points, and leaderboard information. The current Docker starter connects the frontend, backend, and database; authentication and game features will be added as development progresses.

## User Roles

### Students

Students can:

- Select a language and difficulty
- Participate in scavenger-hunt sessions
- Complete location-based challenges
- Earn points and achievements
- View their progress and leaderboard standing

### Teachers

Teachers can:

- Create and manage classes
- Manage student enrollment
- Monitor student progress
- View class-level performance

### Administrators

Administrators manage user accounts and support system maintenance.

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

Lost In Translation aims to make language practice more interactive, contextual, and engaging by moving listening and vocabulary exercises beyond traditional screen-based quizzes.

## Team

**Team 7**
- Gamuchirai Mhere
- Madiba Burks Magara
- Ashish Nayak
- Dan Rukundo
