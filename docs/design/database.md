# Accounts and classes schema

Based on the [Team 7 proposal](../Proposal/499%20-%20Team%207%20Project%20Proposal.md)
and its attached PDF. Backend-managed authentication replaces the proposal's Firebase choice.

| Table | Purpose |
| --- | --- |
| `users` | Unique email/username, names, role and required `password` for every account type |
| `students`, `teachers` | Role-specific details, including unique student numbers |
| `authorized_teacher_emails` | Normalized email allowlist for teacher signup |
| `languages` | Six languages specified in the proposal |
| `classes`, `class_enrollments` | Teacher-owned classes and unique student enrollment |
| `student_languages` | Languages studied independently of class enrollment |
| `schema_migrations` | Applied SQL filenames, checksums and timestamps |

`password` must contain an encoded salted password hash produced by the backend.
The database requires a nonempty value; it cannot verify that a value is securely hashed.
Never store plaintext passwords or return the stored hash in API responses.
Create the user and matching student/teacher record in one transaction; admins need only a user row.
Foreign keys reject mismatched subtypes and prevent students from owning classes.
The backend must still enforce teacher signup authorization and role/ownership checks on requests.
Deleting a user cascades to subtype records and enrollments; deleting a teacher also deletes their classes.

## Apply migrations

With PostgreSQL 17 running, install `src/backend/requirements.txt`, then set `DATABASE_URL`
in your environment or the repository `.env` file. Use the connection URL from the PostgreSQL setup PR.
Run from the repository root:

```sh
python src/backend/migrate.py
```

The runner serializes concurrent runs and applies pending migrations in one transaction.
Rerunning is safe. Never edit an applied SQL file; add a numbered migration instead.
This initial migration targets a fresh application schema, not the old experimental Firebase schema.

Set `TEST_DATABASE_URL` to a disposable PostgreSQL database and run
`python -m pytest tests/backend -q`. Tests create a uniquely named schema, roll back test data,
and remove the schema afterward. CI runs migrations and integration tests against PostgreSQL 17.
Without `TEST_DATABASE_URL`, schema tests skip. Existing application tables are not touched by tests.

Authentication endpoints, password reset, gameplay, points, badges, icons, leaderboards,
debriefs and chatbot tables are deferred to subsequent PRs under the 500-line limit.
