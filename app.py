from flask import Flask, request, jsonify, render_template
import sqlite3
import logging

app = Flask(__name__)
DB = "bank.db"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

log = logging.getLogger(__name__)


# vulnerable — string concatenation
@app.route("/login/vulnerable", methods=["POST"])
def login_vulnerable():
    username = request.json.get("username", "")
    password = request.json.get("password", "")

    # ⚠️ Angreifer-Input fliesst direkt in den Query
    query = (
        "SELECT id, username, role, balance FROM users "
        "WHERE username = '" + username + "' "
        "AND password = '" + password + "'"
    )

    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute(query)          # ← Die Schwachstelle
        rows = cur.fetchall()
        conn.close()
    except sqlite3.OperationalError as e:
        return jsonify({"success": False, "error": str(e), "query": query}), 400

    if rows:
        users = [{"id": r[0], "username": r[1], "role": r[2], "balance": r[3]} for r in rows]
        return jsonify({
            "success": True,
            "query": query,
            "users_returned": len(users),
            "data": users
        })
    return jsonify({"success": False, "query": query, "users_returned": 0})


# safe — prepared statement / parameterized query
@app.route("/login/secure", methods=["POST"])
def login_secure():
    username = request.json.get("username", "")
    password = request.json.get("password", "")

    # ✅ Struktur und Daten sind strikt getrennt
    query = (
        "SELECT id, username, role, balance FROM users "
        "WHERE username = ? AND password = ?"
    )
    params = (username, password)   # ← niemals in den String eingebettet

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(query, params)      # DB escaped params automatisch
    rows = cur.fetchall()
    conn.close()

    if rows:
        user = {"id": rows[0][0], "username": rows[0][1],
                "role": rows[0][2], "balance": rows[0][3]}
        return jsonify({
            "success": True,
            "query": query,
            "params": list(params),
            "data": [user]
        })
    return jsonify({
        "success": False,
        "query": query,
        "params": list(params),
        "users_returned": 0
    })


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    from database import init_db
    init_db()
    app.run(debug=True, port=5000)