from flask import Flask, request, jsonify, render_template
import sqlite3
import os

app = Flask(__name__)
DB_PATH = "hospital1.db"

# Initialize DB: create table if it doesn't exist
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            room_no TEXT NOT NULL,
            floor TEXT NOT NULL,
            department TEXT NOT NULL,
            admitted_on TEXT
        )
    ''')

    # Insert sample data if table is empty
    cur.execute("SELECT COUNT(*) FROM patients")
    if cur.fetchone()[0] == 0:
        sample_data = [
            ('Ramesh', '204', '2nd', 'Cardiology', '2025-10-01'),
            ('Priya', '101', '1st', 'Neurology', '2025-10-05'),
            ('Suresh', '303', '3rd', 'Orthopedic', '2025-10-09'),
            ('Anita', '405', '4th', 'Pediatrics', '2025-10-02'),
            ('Rajesh', '108', '1st', 'ENT', '2025-10-11')
        ]
        cur.executemany('''
            INSERT INTO patients (name, room_no, floor, department, admitted_on)
            VALUES (?, ?, ?, ?, ?)
        ''', sample_data)
        print("✅ Sample data inserted.")
    else:
        print("ℹ️ Patients table already has data.")

    conn.commit()
    conn.close()

# Get patient info by name
def get_patient_info(name):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT room_no, department, floor FROM patients WHERE LOWER(name)=LOWER(?)", (name,))
    result = cur.fetchone()
    conn.close()
    return result

# Get all patients for frontend map
def get_all_patients():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT name, room_no FROM patients")
    result = cur.fetchall()
    conn.close()
    return result

# Initialize database
init_db()

@app.route('/')
def home():
    patients = get_all_patients()
    return render_template("navigation.html", patients=patients)

@app.route('/get_patient', methods=['POST'])
def get_patient():
    data = request.get_json()
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"response": "Please say the patient's name."})

    patient = get_patient_info(name)
    if patient:
        room_no, dept, floor = patient
        response = f"{name} is in room {room_no}, {dept} department, on floor {floor}."
    else:
        response = f"Sorry, no patient named {name} found."
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True)
