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
| Authentication | Firebase Authentication |
| Database | PostgreSQL 17 |
| Frontend Testing | Vitest, React Testing Library |
| Backend Testing | PyTest |

## System Architecture

(Game Name) uses a **React/TypeScript frontend** to provide the interactive game interface and a **Python backend** to handle application logic and services.

**Firebase Authentication** manages user authentication, while a **SQL database** stores structured application data such as users, classes, game progress, points, and leaderboard information.

## Run the Backend and PostgreSQL Locally

Install Python 3.13 and Docker Desktop, and start Docker Desktop. From the repository root:

```sh
cp .env.example .env
docker compose up -d --wait
python3 -m venv .venv
source .venv/bin/activate
pip install -r src/backend/requirements.txt
python src/backend/migrate.py
uvicorn main:app --app-dir src/backend --reload
```

Visit `http://localhost:8000/docs` for the API docs. `GET /api/health/db` checks the database connection.
The migration command creates the tables and seeds the six languages and three difficulty levels.
It is safe to run again; future changes belong in new numbered SQL migration files.

Database connection settings are in `.env` (ignored by Git). When changing the database port or credentials,
update `DATABASE_URL` and `TEST_DATABASE_URL` to match. Docker keeps data in a named volume;
`docker compose stop` stops the database without deleting data. On an existing volume, changing
`POSTGRES_PASSWORD` in `.env` does not change the database password.

Open a PostgreSQL shell:

```sh
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

Run backend and PostgreSQL integration tests with the database running:

```sh
python -m pytest tests/backend -q
```

Integration tests use `TEST_DATABASE_URL` and create a temporary schema, leaving application data untouched.
Without that variable, database integration tests are skipped. CI runs them against PostgreSQL 17.
See [the database design](docs/design/database.md) for tables, relationships, defaults, and backend usage.

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

(Game Name) aims to make language practice more interactive, contextual, and engaging by moving listening and vocabulary exercises beyond traditional screen-based quizzes.

## Team

**Team 7**
- Gamuchirai Mhere
- Madiba Burks Magara
- Ashish Nayak
- Dan Rukundo
