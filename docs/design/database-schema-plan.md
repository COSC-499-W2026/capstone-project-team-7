# Next PR: Adding the database schema

This connection PR adds PostgreSQL configuration, backend connections and health checks.
It does not create account tables or implement signup/login.

The next PR follows the [project proposal](../Proposal/499%20-%20Team%207%20Project%20Proposal.md)
and the attached proposal PDF, with the user's updated requirement replacing Firebase authentication
with backend-managed authentication.

## Initial schema scope

- A shared `users` table for student, teacher and administrator accounts, with unique email
  and username, first/last name, role and a required `password TEXT NOT NULL` field.
- `password` stores only an encoded, salted password hash, never the submitted password.
  Every role uses this same required field; no Firebase UID is needed.
- Student details include a unique student number; teacher details support teacher-owned classes.
- A teacher signup allowlist, language catalog, classes and enrollments cover the proposal's
  authorized teacher signup and roster requirements. Prevent duplicate enrollment and invalid roles.
- A versioned migration command and focused PostgreSQL constraint tests accompany the schema.
  Keep the complete PR below 500 added plus deleted lines, including docs and tests.

## Later work

Implement password hashing/verification, signup, login, logout, email-based password reset,
password changes and role/ownership checks in a separate authentication PR. Never return the
stored password hash in profile or roster responses. Database constraints alone do not authorize requests.

Add gameplay/progress, locations/clues, sessions/attempts, points, badges, profile icons,
leaderboards, debriefs and chatbot storage in further PRs sized below the same limit.
Do not invent campus location data or gameplay defaults absent from the proposal.

Create the schema branch manually after this setup PR is merged into its target branch,
so the schema PR's line count does not include the setup changes.
