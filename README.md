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
- Points, badges, and leaderboards
- Student progress tracking
- Teacher class dashboards and roster management
- Post-game session summaries and debriefs
- Profile customization and point redemption

## Tech Stack

| Component | Technology |
|---|---|
| Frontend | React, TypeScript |
| Backend | Python |
| Authentication |  Hashed Password |
| Database | SQL |
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

### Adding the backend later



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
