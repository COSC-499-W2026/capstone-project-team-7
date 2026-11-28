# Student account details

`GET /api/student/profile` returns the signed-in student's username, student number, classes
(`id`, `name`, `language_code`) and languages (`code`, `name`). Languages combine
explicit study records with enrolled-class languages, without duplicates.
Students with no enrollments or study records receive empty lists.
`profile_icon` is the id of the equipped icon, or null if none is equipped.

The student is identified only by their session; no student ID parameter is
accepted. ID-based profile paths return 404. Missing or expired sessions return
401; teachers/admins receive 403; missing student records receive 404;
database failures receive 503.
Passwords, session tokens and email addresses are not returned. The student number is
returned so the dashboard can show it, and only ever for the signed-in student.


`PATCH /api/student/profile` updates the signed-in student's `first_name`,
`last_name`, or `username` and returns those three fields. Send one or more
fields, such as `{"first_name": "Alex", "username": "alex123"}`. Omitted fields
keep their values. Values are trimmed, and usernames can be up to 50 characters.
Empty requests, blank or null values, and extra fields such as email return 422.
A username already in use, including a case-insensitive match, returns 409.
The same session, role, and profile checks apply as for the read endpoint.
