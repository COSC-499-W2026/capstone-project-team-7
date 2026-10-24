# Student account details

`GET /api/student/profile` returns the signed-in student's username, classes
(`id`, `name`, `language_code`) and languages (`code`, `name`). Languages combine
explicit study records with enrolled-class languages, without duplicates.
Students with no enrollments or study records receive empty lists.
`profile_icon` is returned as null until profile-icon storage is implemented.

`GET /api/student/profile/{student_id}` permits only the signed-in student's ID.
Other IDs return 403 without disclosing whether the account exists. Missing or
expired sessions return 401; teachers/admins receive 403; malformed IDs receive
422; missing student records receive 404; database failures receive 503.
Passwords, session tokens, email addresses and student numbers are not returned.
