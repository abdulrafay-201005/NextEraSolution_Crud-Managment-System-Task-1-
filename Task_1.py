from flask import Flask, request, jsonify, g
import sqlite3
import os

DB_PATH = "users.db"
app = Flask(__name__)

# ---------- DB helpers ----------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    """Create table if not exists."""
    db = sqlite3.connect(DB_PATH)
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL
        )
    """)
    db.commit()
    db.close()

if not os.path.exists(DB_PATH):
    init_db()

# ---------- Routes ----------
@app.route("/users", methods=["GET"])
def list_users():
    db = get_db()
    rows = db.execute("SELECT * FROM users").fetchall()
    users = [dict(r) for r in rows]
    return jsonify(users), 200

@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    db = get_db()
    row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        return jsonify({"error": "User not found"}), 404
    return jsonify(dict(row)), 200

@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json() or {}
    name = data.get("name")
    email = data.get("email")
    if not name or not email:
        return jsonify({"error": "name and email required"}), 400

    db = get_db()
    cursor = db.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))
    db.commit()
    new_id = cursor.lastrowid
    row = db.execute("SELECT * FROM users WHERE id = ?", (new_id,)).fetchone()
    return jsonify(dict(row)), 201

@app.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.get_json() or {}
    name = data.get("name")
    email = data.get("email")
    if not name and not email:
        return jsonify({"error": "provide name or email to update"}), 400

    db = get_db()
    row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        return jsonify({"error": "User not found"}), 404

    new_name = name if name else row["name"]
    new_email = email if email else row["email"]
    db.execute("UPDATE users SET name = ?, email = ? WHERE id = ?", (new_name, new_email, user_id))
    db.commit()
    row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return jsonify(dict(row)), 200

@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    db = get_db()
    row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        return jsonify({"error": "User not found"}), 404
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    return jsonify({"message": "User deleted"}), 200

# ---------- Run server ----------
if __name__ == "__main__":
    app.run(debug=True, port=8000)
