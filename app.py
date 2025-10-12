from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import date as dt

app = Flask(__name__)
app.secret_key = "supersecret"  # required for session

# ---- Database Connection ----
def get_db_connection():
    conn = sqlite3.connect("hospital.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---- Homepage ----
@app.route("/")
def home():
    return render_template("index.html")

# ---- Doctor Availability (Public View) ----
@app.route("/availability", methods=["GET", "POST"])
def view_availability():
    conn = get_db_connection()
    if request.method == "POST":
        selected_day = request.form.get("date")
    else:
        selected_day = dt.today().strftime("%Y-%m-%d")

    doctors = conn.execute("""
        SELECT d.name, d.specialization, a.start_time, a.end_time
        FROM doctors d
        JOIN availability a ON d.doctor_id = a.doctor_id
        WHERE a.day = ?
    """, (selected_day,)).fetchall()
    conn.close()

    return render_template("availability.html", doctors=doctors, date=selected_day)

# ---- Appointment Booking (Patient Side) ----
@app.route("/appointment")
def appointment_booking():
    return render_template("appointment_booking.html")

# ---- Queue Page ----
@app.route("/queue")
def queue():
    return render_template("queue.html")

@app.route("/navigation")
def navigation():
    return render_template("navigation.html")

# ---- Doctor Login ----
@app.route("/doctor/login", methods=["GET", "POST"])
def doctor_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        doctor = conn.execute(
            "SELECT * FROM doctors WHERE email=? AND password=?",
            (email, password)
        ).fetchone()
        conn.close()

        if doctor:
            session["doctor_id"] = doctor["doctor_id"]
            session["doctor_name"] = doctor["name"]
            flash("Login successful!", "success")
            return redirect(url_for("doctor_dashboard"))
        else:
            flash("Invalid email or password", "danger")

    return render_template("doctor_login.html")

# ---- Doctor Dashboard ----
@app.route("/doctor/dashboard")
def doctor_dashboard():
    if "doctor_id" not in session:
        return redirect(url_for("doctor_login"))

    conn = get_db_connection()
    slots = conn.execute(
        "SELECT * FROM availability WHERE doctor_id=? ORDER BY day, start_time",
        (session["doctor_id"],)
    ).fetchall()
    conn.close()

    return render_template("doctor_dashboard.html",
                           doctor=session["doctor_name"],
                           slots=slots)

# ---- Doctor Set Availability ----
@app.route("/doctor/set_availability")
def set_availability():
    if "doctor_id" not in session:
        return redirect(url_for("doctor_login"))
    return render_template("set_availability.html")

# ---- Add Availability Slot ----
@app.route("/doctor/add_availability", methods=["POST"])
def add_availability():
    if "doctor_id" not in session:
        return redirect(url_for("doctor_login"))

    day = request.form["day"]
    start_time = request.form["start_time"]
    end_time = request.form["end_time"]
    status = request.form["status"]

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO availability (doctor_id, day, start_time, end_time, status) VALUES (?,?,?,?,?)",
        (session["doctor_id"], day, start_time, end_time, status)
    )
    conn.commit()
    conn.close()

    flash("Availability slot added successfully!", "success")
    return redirect(url_for("doctor_dashboard"))

# ---- Doctor View Availability ----
@app.route("/doctor/view_availability")
def doctor_view_availability():
    if "doctor_id" not in session:
        flash("Please login first", "danger")
        return redirect(url_for("doctor_login"))

    conn = get_db_connection()
    availability = conn.execute(
        "SELECT id, day, start_time, end_time, status "
        "FROM availability WHERE doctor_id = ? ORDER BY day, start_time",
        (session["doctor_id"],)
    ).fetchall()
    conn.close()

    return render_template("doctor_view_availability.html", availability=availability)

# ---- Delete Availability Slot ----
@app.route("/doctor/delete_availability/<int:slot_id>", methods=["POST"])
def delete_availability(slot_id):
    if "doctor_id" not in session:
        return redirect(url_for("doctor_login"))

    conn = get_db_connection()
    conn.execute("DELETE FROM availability WHERE id=? AND doctor_id=?",
                 (slot_id, session["doctor_id"]))
    conn.commit()
    conn.close()

    flash("Availability slot deleted successfully!", "info")
    return redirect(url_for("doctor_view_availability"))

# ---- Doctor Logout ----
@app.route("/doctor/logout")
def doctor_logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("doctor_login"))

# ---- Run App ----
if __name__ == "__main__":
    app.run(debug=True)
