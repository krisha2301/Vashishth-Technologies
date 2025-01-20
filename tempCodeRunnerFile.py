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
    app.logger.debug(f"Route accessed for division: {division}")
    if not is_logged_in():
        return redirect('/login')
    
    conn = get_db_connection()
    students = conn.execute('SELECT * FROM Students WHERE division = ?', (division,)).fetchall()

    if request.method == 'POST':
        app.logger.debug(f"Form Data: {request.form}") ###
        date = request.form['date']
        
        for student in students:
            student_id = student['id']
            status = request.form.get(f'attendance_{student_id}')

            print(f"Student ID: {student_id}, Date: {date}, Status: {status}")

            if date and status in ('present', 'absent'):
                try:
                    conn.execute('''
                        INSERT OR REPLACE INTO Attendance (student_id, date, status)
                        VALUES (?, ?, ?)''', (student_id, date, status))
                except sqlite3.Error as e:
                    print(f"Database Error for Student ID {student_id}: {e}")
            else:
                print(f"Invalid input for Student ID {student_id}: Status or Date is missing")

            # conn.execute('''INSERT OR REPLACE INTO Attendance (student_id, date, status) 
            #                 VALUES (?, ?, ?)''', (student_id, date, status))
        
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
    
    # Generate attendance report for the entire month for the selected division
    report = {}
    students = conn.execute('SELECT * FROM Students WHERE division = ?', (division,)).fetchall()
    
    for student in students:
        report[student['name']] = {
            'present': 0,
            'absent': 0
        }
        
        attendance = conn.execute('''SELECT * FROM Attendance WHERE student_id = ? AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')''',
                                  (student['id'],)).fetchall()
        
        for record in attendance:
            if record['status'] == 'present':
                report[student['name']]['present'] += 1
            elif record['status'] == 'absent':
                report[student['name']]['absent'] += 1
    
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

@app.route('/test_logging')
def test_logging():
    app.logger.debug("Debug message")
    app.logger.info("Info message")
    app.logger.warning("Warning message")
    app.logger.error("Error message")
    return "Logging test complete. Check your terminal."

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True)