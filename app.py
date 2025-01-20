from flask import Flask, render_template, request, redirect, session
import sqlite3
import logging

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # For handling session (login)

DATABASE = 'C:/Users/HP/Downloads/OnlineAssignment/attendance.db'

# Function to get a database connection
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # This allows column access by name
    return conn

# Check if user is logged in
def is_logged_in():
    return 'role' in session

@app.route('/')
def index():
    # Check if the user is logged in
    if not is_logged_in() or 'role' not in session:
        return redirect('/login')
    
    conn = get_db_connection()
    
    # Define divisions
    divisions = ['Div A', 'Div B']
    
    conn.close()
    return render_template('index.html', divisions=divisions)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM Users WHERE username = ? AND password = ?', 
                            (username, password)).fetchone()
        
        conn.close()
        if user:
            session['username'] = username
            session['role'] = user['role']
            return redirect('/')
        else:
            error = "Unsuccessful Login. Check the Credentials"
            return render_template('login.html', error=error)
    return render_template('login.html')

@app.route('/div/<string:division>', methods=['GET', 'POST'])
def division_page(division):
    # Check if the user is logged in
    if not is_logged_in():
        return redirect('/login')
    
    conn = None
    try:
        conn = get_db_connection()

        # Fetch students by division from the database
        students = conn.execute('SELECT * FROM Students WHERE division = ?', (division,)).fetchall()

        # Check user role and render the appropriate template
        role = session.get('role')  # Get the role from the session
        
        if role == 'admin':
            return render_template('admin_division.html', students=students, division=division)
        elif role == 'professor':
            return render_template('professor_division.html', students=students, division=division)
        else:
            # If the role is unrecognized, redirect to the login page
            return redirect('/login')
    except Exception as e:
        # Log the error for debugging
        print(f"Error in division_page: {str(e)}")
        return f"An error occurred: {str(e)}", 500
    finally:
        # Ensure the database connection is closed
        if conn:
            conn.close()

@app.route('/mark_attendance/<division>', methods=['GET', 'POST'])
def mark_attendance(division):
    app.logger.debug(f"Route accessed for division: {division}")  # Check if the route is triggered
    if not is_logged_in():
        app.logger.debug("User not logged in, redirecting to login page.")
        return redirect('/login')
    
    conn = get_db_connection()
    students = conn.execute('SELECT * FROM Students WHERE division = ?', (division,)).fetchall()

    if request.method == 'POST':
        app.logger.debug(f"POST request received. Form Data: {request.form}")
        date = request.form['date']
        app.logger.debug(f"Date received: {date}")

        for student in students:
            student_id = student['id']
            status = request.form.get(f'attendance_{student_id}')
            app.logger.debug(f"Student ID: {student_id}, Status: {status}")
            
            # Log the attendance details
            if status:
                app.logger.debug(f"Marking attendance for Student ID: {student_id} on {date} with status {status}")
            
            # Insert into Attendance table
            if status in ['present', 'absent']:
                try:
                    conn.execute('''
                        INSERT OR REPLACE INTO Attendance (student_id, date, status)
                        VALUES (?, ?, ?)''', (student_id, date, status))
                    app.logger.debug(f"Attendance for Student ID: {student_id} recorded successfully.")
                except sqlite3.Error as e:
                    app.logger.error(f"Error inserting attendance for Student ID: {student_id}. Error: {e}")
            
        conn.commit()
        conn.close()
        return redirect(f'/div/{division}')

    conn.close()
    return render_template('mark_attendance.html', students=students, division=division)

@app.route('/generate_report/<division>', methods=['GET'])
def generate_report(division):
    if not is_logged_in():
        return redirect('/login')
    
    conn = get_db_connection()

    # Fetch attendance grouped by student, year, and month
    query = '''
        SELECT 
            s.name AS student_name, 
            strftime('%Y', a.date) AS year, 
            strftime('%m', a.date) AS month, 
            a.status, 
            COUNT(*) AS count
        FROM Attendance a
        JOIN Students s ON a.student_id = s.id
        WHERE s.division = ?
        GROUP BY student_name, year, month, a.status
        ORDER BY year, month, student_name
    '''
    attendance_data = conn.execute(query, (division,)).fetchall()

    # Organize attendance data
    report = {}
    for record in attendance_data:
        year = record['year']
        month = record['month']
        student_name = record['student_name']
        status = record['status']
        count = record['count']

        # Convert numeric month to short name (e.g., "01" -> "Jan")
        month_name = {
            "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
            "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
            "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec"
        }[month]

        # Initialize structure if missing
        if year not in report:
            report[year] = {}
        if month_name not in report[year]:
            report[year][month_name] = {}
        if student_name not in report[year][month_name]:
            report[year][month_name][student_name] = {'present': 0, 'absent': 0}

        # Increment present or absent counts
        if status == 'present':
            report[year][month_name][student_name]['present'] += count
        elif status == 'absent':
            report[year][month_name][student_name]['absent'] += count

    conn.close()
    return render_template('attendance_report.html', report=report, division=division)

@app.route('/add_student/<division>', methods=['GET', 'POST'])
def add_student(division):
    if not is_logged_in() or session['role'] != 'admin':
        return redirect('/login')
    
    if request.method == 'POST':
        name = request.form['name']
        conn = get_db_connection()
        conn.execute('INSERT INTO Students (name, division) VALUES (?, ?)', (name, division))
        conn.commit()
        conn.close()
        return redirect(f'/div/{division}')
    
    return render_template('add_student.html', division=division)

@app.route('/remove_student/<division>/<int:student_id>', methods=['GET', 'POST'])
def remove_student(division, student_id):
    if not is_logged_in() or session['role'] != 'admin':
        return redirect('/login')
    
    conn = get_db_connection()
    conn.execute('DELETE FROM Students WHERE id = ?', (student_id,))
    conn.commit()
    conn.close()
    
    return redirect(f'/div/{division}')

# @app.route('/test_insert', methods=['GET', 'POST'])
# def test_insert():
#     conn = get_db_connection()
#     try:
#         conn.execute('''
#             INSERT OR REPLACE INTO Attendance (student_id, date, status)
#             VALUES (1, '2025-01-17', 'absent')''')
#         conn.commit()
#         return "Insert successful"
#     except sqlite3.Error as e:
#         return f"Insert failed: {e}"
#     finally:
#         conn.close()

@app.route('/debug', methods=['GET', 'POST'])
def debug():
    if request.method == 'POST':
        app.logger.debug(f"POST Data: {request.form}")
    return "Debug route reached!"

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True)