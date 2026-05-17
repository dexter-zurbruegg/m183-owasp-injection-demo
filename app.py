from flask import Flask, request, jsonify, render_template
import sqlite3
import logging

app = Flask(__name__)
DB = "bank.db"

log = app.logger
log.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
))
log.addHandler(handler)


# VULNERABLE — string concatenation (NEVER do this in production!)
@app.route("/login/vulnerable", methods=["POST"])
def login_vulnerable():
    username = request.json.get("username", "")
    password = request.json.get("password", "")

    # ⚠️ Attacker input flows directly into the query
    query = (
        "SELECT id, username, role, balance FROM users "
        "WHERE username = '" + username + "' "
        "AND password = '" + password + "'"
    )

    log.warning("VULNERABLE endpoint called")
    log.warning("  Input   → username: %r | password: %r", username, password)
    log.warning("  Query   → %s", query)

    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute(query)          # ← The vulnerability
        rows = cur.fetchall()
        conn.close()
    except sqlite3.OperationalError as e:
        log.error("  DB Error → %s", e)
        return jsonify({"success": False, "error": str(e), "query": query}), 400

    if rows:
        users = [{"id": r[0], "username": r[1], "role": r[2], "balance": r[3]} for r in rows]
        log.warning("  Result  → %d row(s) returned — ATTACK LIKELY SUCCEEDED", len(users))
        for u in users:
            log.warning("            dumped: %s (role=%s, balance=%s)", u["username"], u["role"], u["balance"])
        return jsonify({
            "success": True,
            "query": query,
            "users_returned": len(users),
            "data": users
        })

    log.info("  Result  → 0 rows returned")
    return jsonify({"success": False, "query": query, "users_returned": 0})


# SECURE — prepared statement / parameterized query
@app.route("/login/secure", methods=["POST"])
def login_secure():
    username = request.json.get("username", "")
    password = request.json.get("password", "")

    # ✅ Structure and data are strictly separated
    query = (
        "SELECT id, username, role, balance FROM users "
        "WHERE username = ? AND password = ?"
    )
    params = (username, password)   # ← never embedded in the string

    log.info("SECURE endpoint called")
    log.info("  Input   → username: %r | password: %r", username, password)
    log.info("  Query   → %s", query)
    log.info("  Params  → %r  (passed separately, never interpolated)", params)

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(query, params)      # DB escapes params automatically
    rows = cur.fetchall()
    conn.close()

    if rows:
        user = {"id": rows[0][0], "username": rows[0][1],
                "role": rows[0][2], "balance": rows[0][3]}
        log.info("  Result  → login successful for %r", user["username"])
        return jsonify({
            "success": True,
            "query": query,
            "params": list(params),
            "data": [user]
        })

    log.info("  Result  → 0 rows — attack blocked or wrong credentials")
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
    log.info("Bank demo app starting on http://localhost:5000")
    app.run(debug=True, port=5000)