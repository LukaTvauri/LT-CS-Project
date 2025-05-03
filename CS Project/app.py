from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3, os
from words import random_word

app = Flask(__name__)
app.secret_key = "supersecretkey"

def init_db():
    if not os.path.exists("users.db"):
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)")
        conn.commit()
        conn.close()

init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        with sqlite3.connect("users.db") as conn:
            c = conn.cursor()
            c.execute("SELECT 1 FROM users WHERE username=? AND password=?", (username, password))
            if c.fetchone():
                session["username"] = username
                return redirect(url_for("dashboard"))
        flash("Invalid credentials.")
        return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm  = request.form["confirm_password"]
        if password != confirm:
            flash("Passwords do not match.")
            return redirect(url_for("register"))
        try:
            with sqlite3.connect("users.db") as conn:
                c = conn.cursor()
                c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            session["username"] = username
            return redirect(url_for("dashboard"))
        except sqlite3.IntegrityError:
            flash("Username already exists.")
            return redirect(url_for("register"))
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if "username" in session:
        return render_template("dashboard.html", username=session["username"])
    return redirect(url_for("login"))

@app.route("/difficulty")
def difficulty():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("difficulty.html")

@app.route("/word_game")
def word_game():
    if "username" not in session:
        return redirect(url_for("login"))
    level = request.args.get("level", "medium")
    start_points = {"easy": 2000, "medium": 1400, "hard": 800}.get(level, 1400)
    picked = random_word()
    session.update(
        game_word      = picked["word"],
        game_mask      = ["_" for _ in picked["word"]],
        game_points    = start_points,
        game_whole_try = False,
        used_letters   = []
    )
    return render_template(
        "word_game.html",
        definition = picked["def"],
        masked     = " ".join(session["game_mask"]),
        points     = session["game_points"]
    )

@app.route("/spin", methods=["POST"])
def spin():
    delta = int(request.get_json().get("delta", 0))
    session["game_points"] += delta
    allow = delta > 0
    return jsonify({"points": session["game_points"], "allow": allow, "lost": session["game_points"] <= 0})

@app.route("/guess_letter", methods=["POST"])
def guess_letter():
    letter = request.get_json().get("letter", "").lower()
    if letter in session["used_letters"]:
        return jsonify({"error": "used"})
    session["used_letters"].append(letter)
    cost = 100 if letter in "etano" else 50
    session["game_points"] -= cost
    word = session["game_word"]
    mask = session["game_mask"]
    if letter in word:
        for i, ch in enumerate(word):
            if ch == letter:
                mask[i] = ch.upper()
    finished = "_" not in mask
    return jsonify({"mask": " ".join(mask), "points": session["game_points"], "finished": finished, "lost": session["game_points"] <= 0})

@app.route("/guess_word", methods=["POST"])
def guess_word():
    attempt = request.get_json().get("attempt", "").lower()
    if session["game_whole_try"]:
        return jsonify({"status": "used"})
    session["game_whole_try"] = True
    if attempt == session["game_word"]:
        session["game_mask"] = [ch.upper() for ch in attempt]
        return jsonify({"status": "win", "points": session["game_points"], "display": " ".join(session["game_mask"])})
    session["game_points"] = 0
    return jsonify({"status": "lose", "points": 0})

if __name__ == "__main__":
    app.run(debug=True)
