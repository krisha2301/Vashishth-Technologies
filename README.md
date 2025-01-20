# Vashishth-Technologies
# Online Assignment

Attendance Management Portal - A simple web application for managing student attendance using Python Flask and SQLite.

Features
User Login: Admin and professor roles for access control.
Mark Attendance: Professors can mark attendance for students by selecting the date and marking their presence or absence.
Attendance Report: View monthly attendance reports for students in different divisions.
Student Management: Admins can add and remove students in each division.
Technologies Used
Backend: Flask (Python web framework)
Database: SQLite
Frontend: HTML, Jinja2 for templating
Session Management: Flask sessions for user authentication

Endpoints
GET /: Landing page (Divisions overview)
GET /login: User login page
POST /login: Handle user login
GET /div/<division>: View students in a division (based on user role)
GET /mark_attendance/<division>: Page to mark attendance for students
POST /mark_attendance/<division>: Submit attendance for students
GET /generate_report/<division>: View monthly attendance report for a division
GET /add_student/<division>: Page to add a new student to a division (admin only)
POST /add_student/<division>: Add new student to a division (admin only)
GET /remove_student/<division>/int:student_id: Remove a student from a division (admin only)
GET /logout: Logout the current user

User Roles
Admin: Can add/remove students from divisions.
Professor: Can mark attendance and view attendance reports.
