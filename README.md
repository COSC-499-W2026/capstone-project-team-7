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
- **Backend (Python):** Receives requests through an HTTPS REST API and handles authorization, game sessions, GPS validation, room-number recognition, audio, chatbot integration, class management, and points and rewards. The diagram specifies JWT and role-based access; manual authentication using hashed passwords in PostgreSQL
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

### Room-number OCR

Install optional CPU OCR dependencies with
`pip install -r src/backend/requirements-ocr.txt` in the backend environment.
Pillow is included in the base requirements so decoding and unit tests work without the models.
Docker installs OCR and native libraries; rebuild/restart with `docker compose up -d --build backend` before the demo.
PaddleOCR downloads model weights on first use; that machine needs internet access
and a writable model cache. Subsequent calls reuse one engine per Python process.

`utils.ocr.extract_room_numbers(photo_bytes)` accepts JPEG/PNG photos up to 5 MiB
and 20 million pixels. It returns distinct candidates with confidence at least 0.8.
`UNC`, `FIP`, `COM`, `ASC`, `ART`, `CCS`, `ADM`, `SCI`, `LIB` require a space and three digits (e.g. `LIB 308`).
Only `EME` requires four digits (e.g. `EME 0050`); leading zeros are preserved. Other building codes are rejected.
Letters are uppercased and whitespace normalized; adjacent OCR text boxes can form one identifier.
No readable number returns `[]`; invalid photos raise `InvalidPhoto` and runtime/model
failures raise `OCRUnavailable`. Temporary images are deleted after processing.
The photo verification API compares recognized identifiers with the student's current target.
Run `python -m pytest tests/backend/test_ocr.py -q`; unit tests use fake predictions, not real OCR.

Database connection settings are in `.env` (ignored by Git). When changing the database port or credentials,
update `DATABASE_URL` to match. Docker keeps data in a named volume;
`docker compose stop` stops the database without deleting data. On an existing volume, changing
`POSTGRES_PASSWORD` in `.env` does not change the database password.

Open a PostgreSQL shell:

```sh
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

`StudentSignupRequest` in `src/backend/schemas.py` validates email, password, first/last
name, student number and username. Profile text is trimmed; passwords are preserved.
The full email address is lowercased to match case-insensitive account lookups and uniqueness.
The signup password policy is at least 8 characters, not all whitespace, and at most
72 UTF-8 bytes to match bcrypt. Usernames allow up to 50 characters and student numbers
up to 30, matching PostgreSQL. Unknown fields (including `role`) are rejected.
Duplicate checks and account persistence will be added with the signup service and endpoint.

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

### Admin class enrollment API

A logged-in administrator can enroll a registered student in any class with `POST /api/admin/classes/{uuid}/students` and `{"student_number": "..."}`.
Success returns 201 with `class_id`, `student_id`, and `student_number`. Errors: 401 no session, 403 non-admins, 404 `"Class not found"`, 404 `"Student not found"`,
409 `"Student already enrolled"`, 422 blank or over-long student number or invalid UUID, 503 database failure.
Run `python -m pytest tests/backend/test_admin_enrollment.py -v`; the integration test runs when `DATABASE_URL` is set.

### Teacher approvals API

An administrator can approve teacher signup with `POST /api/admin/approved-teachers`
and JSON `{"email": "teacher@example.com"}`, using the existing `session` cookie.
Emails are trimmed and lowercased. Success returns 201 with `email` and `approved: true`.
Missing, invalid, or expired sessions return 401; non-admins get 403; duplicate approvals
get 409; invalid input gets 422; database failures get 503. Approval enables teacher signup.
No schema migration is required. Integration tests use `TEST_DATABASE_URL` and temporary schemas:
`python -m pytest tests/backend/test_teacher_approval.py -v`.

### Admin accounts API

A logged-in administrator can add another admin with `POST /api/admin/admins`, sending `email`, `username`, `password`, `first_name`, and `last_name`.
Fields follow the teacher signup rules. Success returns 201 with `id`, `email`, `username`, and `role: "admin"`; the new admin can log in right away.
Missing, invalid, or expired sessions return 401; non-admins get 403; a taken email or username gets 409; invalid input gets 422; database failures get 503.
Run `python -m pytest tests/backend/test_admin_creation.py -v`; the login integration test runs when `DATABASE_URL` is set.

### Password reset email API

`POST /api/auth/forgot-password` accepts `{"email":"student@example.com"}` without login.
Registered, unknown, and cooldown requests return the same generic 200 message; invalid input gets 422 and database failures get 503.
Only token hashes are stored. Links expire after 30 minutes; each account is limited atomically to one email per minute and five per rolling hour, even after a token is consumed.
Run `python src/backend/migrate.py`. Set `SMTP_USERNAME`, `SMTP_APP_PASSWORD`, and `FRONTEND_URL` in your ignored `.env`.
Enable Gmail 2-Step Verification and generate an App Password. Use your deployed HTTPS frontend URL in production.
Delivery runs after the response; SMTP/configuration failures log a generic warning. Frontend forms are separate.
`POST /api/auth/reset-password` accepts `{"token":"<emailed token>","new_password":"<new password>"}` without login.
Passwords follow signup rules: at least 8 characters, not all whitespace, and at most 72 UTF-8 bytes.
Success returns 200, consumes the token, clears the session cookie, and revokes all sessions for that account; log in again.
Invalid, expired, replaced, or already-used links return the same 422 error. Database failures return 503 without partial changes.

### Current user API

`GET /api/auth/me` reads the `session` cookie and returns 200 with `email`, `first_name`, `role`, and `redirect_to`; it does not return the password hash.
A missing, expired, or logged-out session returns 401 `"Unauthorized"`; 503 if the database is down.
Protected routes reuse the same check with `Depends(current_user)` from `auth.py`.

### Change password API

`POST /api/auth/change-password` accepts `current_password` and `new_password` with a valid `session` cookie.
All account roles can change their own password. New passwords follow the signup policy: 8+ characters,
not all whitespace, and at most 72 UTF-8 bytes. Success returns 200 with `"Password changed. Please log in again."`,
clears the cookie, and revokes every session for the user in the same transaction as the password update.
Errors: 401 missing/invalid/expired session, 403 incorrect current password, 422 invalid input, 503 database failure.
Teacher class access and teacher signup approvals reuse `auth.current_user` for
session validation. Class routes enforce `require_teacher`; approval uses the
shared `require_admin`. Invalid sessions return 401 `"Unauthorized"`; non-admin
approval requests return 403 `"Forbidden"`. Authentication runs before body
validation, so unauthenticated approval requests return 401 even with invalid input.

### Teacher class access API

After login, `GET /api/teacher/classes` lists assigned classes; `GET /api/teacher/classes/{uuid}` returns one assigned class.
`POST /api/teacher/classes` with `name` and `language_code` creates a class owned by the teacher and returns 201; a blank name or unknown language returns 422.
All use the existing `session` cookie: 401 for missing/invalid/expired sessions, 403 for non-teachers, 404 for unassigned/missing classes, and 503 for database failures.
Responses include `id`, `name`, `language_code`, and `class_code`; no assigned classes returns `[]`. Use HTTPS for the Secure login cookie.
Run `python -m pytest tests/backend/test_teacher_access.py -v` with `TEST_DATABASE_URL` set; integration tests use temporary schemas and real login.

### Student deletion API

An administrator can delete a student with `DELETE /api/admin/students/{uuid}`, using the existing `session` cookie.
The student's enrollments, languages and sessions are removed with the account; their classes are kept.
Success returns 204; 401/403 for missing sessions or non-admins, 404 for unknown ids or non-student accounts, 503 for database failures.
### Teacher deletion API

An administrator can delete a teacher with `DELETE /api/admin/teachers/{uuid}`, using the existing `session` cookie.
Deleting a class removes its student enrollments, so the request is refused with 409 until every class has been reassigned
with `PATCH /api/admin/classes/{uuid}/teacher`. Success returns 204; 401/403 for missing sessions or non-admins, 404 for unknown teachers, 503 for database failures.
### Class enrollment API

`POST /api/teacher/classes/{uuid}/students` with `{"student_number": "..."}` enrolls a registered student and returns 201 with `class_id`, `student_id`, and `student_number`.
Only teachers can enroll, and only into classes they own. Errors: 401 no session, 403 students and admins, 404 `"Class not found"` (missing or another teacher's class),
404 `"Student not found"` (no student has that number), 409 `"Student already enrolled"`, 422 blank or over-long student number, 503 database failure.
`DELETE /api/teacher/classes/{uuid}/students/{student_id}` removes the enrollment and returns 204; the student's account is kept.
Same auth rules. Errors: 404 `"Class not found"`, 404 `"Student not enrolled"`, 422 invalid UUID, 503 database failure.
Run `python -m pytest tests/backend/test_class_enrollment.py -v` with `TEST_DATABASE_URL` set.

### Class roster API

`GET /api/teacher/classes/{uuid}/students` lists the enrolled students, ordered by lastname. Each has `student_id`, `username`, `first_name`, `last_name`, and `student_number`.
A class with no students returns `[]`. Same auth rules. Errors: 404 `"Class not found"` (missing or another teacher's class), 422 invalid UUID, 503 database failure.
Run `python -m pytest tests/backend/test_class_roster.py -v` with `TEST_DATABASE_URL` set.

### Student class join API

After login, a student can `POST /api/student/classes/join` with `{"class_code": "ABC123DEF456"}` to enrol themselves; the code is trimmed and uppercased.
Success returns 201 with the class `id`, `name`, and `language_code`. An unknown code returns 404 `"Class not found"`, joining twice returns 409 `"Already enrolled"`, and a blank or over-long code returns 422.
Missing/invalid/expired sessions return 401, non-students get 403, and database failures return 503.
Run `python -m pytest tests/backend/test_student_enrollment.py -v` with `TEST_DATABASE_URL` set.

### Game session API

After login, a student can `POST /api/game/start` to start a game. For now every game is French (`fr`) at Basic difficulty.
The backend picks 5 random locations that have a French clue and saves them in order in `game_sessions` and `game_session_locations`.
Success returns 201 with `game_id`, `language_code`, `difficulty`, `current_position` (1), and `total_locations` (5); locations and clues are not returned.
Fewer than 5 French locations returns 409 `"Not enough locations for this language yet"` and saves nothing.
Missing/invalid/expired sessions return 401, non-students get 403, and database failures return 503. Deleting a student keeps their games with no student linked.
Run `python -m pytest tests/backend/test_game_session.py -v` with `TEST_DATABASE_URL` set.

After starting, `GET /api/game/{game_id}/clue` returns the current clue: `position`, `total_locations`, `building`, and `audio_url`.
`GET /api/game/{game_id}/clue/audio` plays that clue's audio (`audio_url` adds `?position=<n>` so each clue gets a new link). Audio files are kept in the backend (`src/backend/audio/<language>/`) and
never linked by name, so neither the clue nor the audio link reveals the room number.
Another student's game or an unknown id returns 404 `"Game not found"`, a finished game returns 409, an invalid id returns 422.
A missing audio file returns 404 `"Audio not found for this clue"`.

`POST /api/game/{game_id}/answer` takes the photo as the request body (e.g. `Content-Type: image/jpeg`, up to 5 MiB).
Each valid photo counts an attempt. A correct match awards 10 points; incorrect/unreadable photos award zero. Attempts and difficulty do not affect points.
A correct answer moves to the next spot; the 5th correct answer finishes the game. Returns `correct`, `attempts`, `finished`, `next_position`, `points_awarded`, `total_points` (game total), and `message`.
Apply `007_photo_verification_points.sql` and install the optional OCR requirements. Full building/room identifiers must match; points and progress commit together, preventing duplicate awards. GPS is outside this change.
Errors: 422 no photo, 413 photo too large, 404 not your game, 409 game finished or spot already answered, 503 OCR/database failure.

### Demo locations and audio

After running migrations, add the 5 demo locations and their French clues (safe to run again):

```sh
docker compose exec backend python -m utils.seed_locations   # or: cd src/backend && python -m utils.seed_locations
```

The French audio clues live in `src/backend/audio/fr/`, named by building and room (e.g. `COM-316.mp3`).
To remake them: `pip install edge-tts`, then `cd src/backend && python -m utils.generate_audio`.
Tests: `python -m pytest tests/backend/test_seed_locations.py tests/backend/test_generate_audio.py -v` (seed tests need `TEST_DATABASE_URL`).

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

### Photo verification feedback

The live-camera page submits the captured JPEG to `/api/game/{game_id}/answer` with the login cookie.
While checking, submission, retake and close controls are disabled. Correct matches show server-awarded
points and the game total on the next clue; the existing finish screen shows the total after the final location.
Incorrect/unreadable photos show zero awarded points and allow retaking; upload/network/OCR errors allow retry.
This flow requires the backend verification API with `points_awarded`, `total_points` and `message` fields.

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

## Backend API

### Student registration

`POST /api/auth/student/signup` accepts `email`, `password`, `first_name`, `last_name`,
`student_number`, and `username`. All fields are required. Emails are validated and
lowercased; profile text is trimmed. Passwords keep their original whitespace and require
at least 8 characters, some non-whitespace text, and at most 72 UTF-8 bytes.
Usernames allow up to 50 characters and student numbers up to 30. Extra fields are rejected.

Success returns **201** with `{"id": "<user UUID>", "role": "student"}`.
The frontend can then send the student to login; signup does not create a session.
Errors: **409** `"Account details already in use"` for duplicate email, username or student
number; **422** for invalid input; **503** `"Database unavailable"` for database failures.

`registration.create_student` saves validated signup fields in PostgreSQL with role `student`
and the existing bcrypt password hash. User and student rows commit together; duplicate
email, username or student number raises `DuplicateStudentAccount` without leaving partial data.
Registration tests use a temporary schema in `TEST_DATABASE_URL` (or local `DATABASE_URL`).
The endpoint passes validated fields with `create_student(**request.model_dump())`.
After installing backend dependencies and running `python src/backend/migrate.py`, try
signup through `http://localhost:8000/docs`. Run endpoint tests with
`python -m pytest tests/backend/test_student_signup.py -q`.

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
