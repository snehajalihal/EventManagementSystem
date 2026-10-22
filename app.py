from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)

app.secret_key = os.environ.get("FLASK_SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("FLASK_SECRET_KEY environment variable is not set.")

csrf = CSRFProtect(app)

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "events.db")

def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    connection = get_db_connection()
    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
    """)


    connection.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            event_date TEXT NOT NULL,
            location TEXT NOT NULL,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """)


    connection.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            event_id INTEGER NOT NULL,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, event_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (event_id) REFERENCES events(id)
        )
    """)

    connection.commit()
    connection.close()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not name or not email or len(password) < 8:
            return "Enter your name, a valid email, and a password of at least 8 characters.", 400

        connection = get_db_connection()
        try:
            connection.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, generate_password_hash(password))
            )
            connection.commit()
        except sqlite3.IntegrityError:
            connection.close()
            return "This email is already registered. Please log in.", 409

        connection.close()
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        connection = get_db_connection()
        user = connection.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        connection.close()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["role"] = user["role"]
            return redirect(url_for("events"))

        return "Invalid email or password. Please try again.", 401

    return render_template("login.html")



@app.route("/events")
def events():
    search_query = request.args.get("search", "").strip()
    location_filter = request.args.get("location", "").strip()

    connection = get_db_connection()

    all_events = connection.execute("""
        SELECT events.*,
               registrations.id AS registration_id
        FROM events
        LEFT JOIN registrations
            ON events.id = registrations.event_id
            AND registrations.user_id = ?
        WHERE events.title LIKE ?
          AND events.location LIKE ?
        ORDER BY events.event_date
    """, (
        session.get("user_id", -1),
        f"%{search_query}%",
        f"%{location_filter}%"
    )).fetchall()

    connection.close()

    return render_template(
        "events.html",
        events=all_events,
        search_query=search_query,
        location_filter=location_filter
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/admin/events", methods=["GET", "POST"])
def admin_events():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        return "Access denied. Admin permission required.", 403

    message = ""

    connection = get_db_connection()

    total_events = connection.execute(
        "SELECT COUNT(*) FROM events"
    ).fetchone()[0]

    total_users = connection.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    total_registrations = connection.execute(
        "SELECT COUNT(*) FROM registrations"
    ).fetchone()[0]

    popular_events = connection.execute("""
        SELECT events.title, COUNT(registrations.id) AS registration_count
        FROM events
        LEFT JOIN registrations
            ON events.id = registrations.event_id
        GROUP BY events.id
        ORDER BY registration_count DES
    connection.close()

    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form["description"].strip()
        event_date = request.form["event_date"]
        location = request.form["location"].strip()

        if not title or not description or not event_date or not location:
            message = "Please fill in all fields."
        else:
            connection = get_db_connection()
            connection.execute(
                """INSERT INTO events
                   (title, description, event_date, location, created_by)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    title,
                    description,
                    event_date,
                    location,
                    session["user_id"]
                )
            )
            connection.commit()
            connection.close()

            return redirect(url_for("events"))

    return render_template(
    "admin.html",
    message=message,
    total_events=total_events,
    total_users=total_users,
    total_registrations=total_registrations,
    popular_events=popular_events
)

@app.route("/register-event/<int:event_id>", methods=["POST"])
def register_event(event_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    event = connection.execute(
        "SELECT id FROM events WHERE id = ?", (event_id,)
    ).fetchone()

    if event is None:
        connection.close()
        return "Event not found.", 404

    try:
        connection.execute(
            "INSERT INTO registrations (user_id, event_id) VALUES (?, ?)",
            (session["user_id"], event_id)
        )
        connection.commit()
        message = "Successfully registered for the event!"

    except sqlite3.IntegrityError:
        message = "You have already registered for this event."

    finally:
        connection.close()

    return message + ' <a href="/events">Back to Events</a>'


@app.route("/my-registrations")
def my_registrations():
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    my_events = connection.execute("""
        SELECT events.title,
               events.description,
               events.event_date,
               events.location,
               registrations.registered_at
        FROM registrations
        JOIN events ON registrations.event_id = events.id
        WHERE registrations.user_id = ?
        ORDER BY events.event_date
    """, (session["user_id"],)).fetchall()

    connection.close()

    return render_template(
        "my_registrations.html",
        events=my_events
    )


@app.route("/admin/events/edit/<int:event_id>", methods=["GET", "POST"])
def edit_event(event_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        return "Access denied. Admin permission required.", 403

    connection = get_db_connection()

    event = connection.execute(
        "SELECT * FROM events WHERE id = ?", (event_id,)
    ).fetchone()

    if event is None:
        connection.close()
        return "Event not found.", 404

    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form["description"].strip()
        event_date = request.form["event_date"]
        location = request.form["location"].strip()

        if not title or not description or not event_date or not location:
            connection.close()
            return "Please fill in all fields.", 400


        connection.execute(
            """UPDATE events
               SET title = ?, description = ?, event_date = ?, location = ?
               WHERE id = ?""",
            (title, description, event_date, location, event_id)
        )


        connection.commit()
        connection.close()

        return redirect(url_for("events"))

    connection.close()
    return render_template("edit_event.html", event=event)


@app.route("/admin/events/delete/<int:event_id>", methods=["POST"])
def delete_event(event_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        return "Access denied. Admin permission required.", 403

    connection = get_db_connection()

    event = connection.execute(
        "SELECT id FROM events WHERE id = ?", (event_id,)
    ).fetchone()

    if event is None:
        connection.close()
        return "Event not found.", 404

    connection.execute(
        "DELETE FROM registrations WHERE event_id = ?",
        (event_id,)
    )

    connection.execute(
        "DELETE FROM events WHERE id = ?",
        (event_id,)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("events"))


initialize_database()

if __name__ == "__main__":
    app.run(debug=False)