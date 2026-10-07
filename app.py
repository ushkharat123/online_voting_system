from flask import Flask, render_template, request, redirect, session, url_for
import psycopg2

app = Flask(__name__)

# Secret key for session
app.secret_key = "online-voting-secret-key"


# ==========================================
# PostgreSQL DATABASE CONNECTION
# ==========================================

def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="voting_db",
        user="postgres",
        password="tanu123"
    )
    return conn


# ==========================================
# HOME PAGE
# ==========================================

@app.route("/")
def index():
    return render_template("index.html")


# ==========================================
# REGISTER PAGE
# ==========================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()

        try:

            cur.execute(
                """
                INSERT INTO voters (name, email, password)
                VALUES (%s, %s, %s)
                """,
                (name, email, password)
            )

            conn.commit()

            cur.close()
            conn.close()

            return redirect(url_for("login"))

        except Exception as e:

            conn.rollback()
            cur.close()
            conn.close()

            return f"Registration Error: {e}"

    return render_template("register.html")


# ==========================================
# LOGIN PAGE
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT id, name, has_voted
            FROM voters
            WHERE email = %s AND password = %s
            """,
            (email, password)
        )

        voter = cur.fetchone()

        cur.close()
        conn.close()

        if voter:

            session["voter_id"] = voter[0]
            session["voter_name"] = voter[1]
            session["has_voted"] = voter[2]

            return redirect(url_for("vote"))

        else:

            return "Invalid email or password!"

    return render_template("login.html")


# ==========================================
# VOTE PAGE
# ==========================================

@app.route("/vote", methods=["GET", "POST"])
def vote():

    if "voter_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()

    # Check whether voter has already voted
    cur.execute(
        "SELECT has_voted FROM voters WHERE id = %s",
        (session["voter_id"],)
    )

    voter_status = cur.fetchone()

    if voter_status and voter_status[0]:

        cur.close()
        conn.close()

        return render_template(
            "vote.html",
            candidates=[],
            message="You have already voted!"
        )

    if request.method == "POST":

        candidate_id = request.form["candidate"]

        # Insert vote
        cur.execute(
            """
            INSERT INTO votes (voter_id, candidate_id)
            VALUES (%s, %s)
            """,
            (session["voter_id"], candidate_id)
        )

        # Update voter status
        cur.execute(
            """
            UPDATE voters
            SET has_voted = TRUE
            WHERE id = %s
            """,
            (session["voter_id"],)
        )

        conn.commit()

        cur.close()
        conn.close()

        session["has_voted"] = True

        return redirect(url_for("results"))

    # Get candidates
    cur.execute(
        "SELECT id, name, party FROM candidates ORDER BY id"
    )

    candidates = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "vote.html",
        candidates=candidates,
        message=None
    )


# ==========================================
# RESULTS PAGE
# ==========================================

@app.route("/results")
def results():

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            candidates.name,
            candidates.party,
            COUNT(votes.id) AS total_votes
        FROM candidates
        LEFT JOIN votes
        ON candidates.id = votes.candidate_id
        GROUP BY candidates.id, candidates.name, candidates.party
        ORDER BY total_votes DESC
        """
    )

    results_data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "results.html",
        results=results_data
    )

# ==========================================
# ADMIN - SHOW CANDIDATES
# ==========================================

@app.route("/admin")
def admin():

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, name, party FROM candidates ORDER BY id"
    )

    candidates = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "admin.html",
        candidates=candidates
    )


# ==========================================
# ADD CANDIDATE
# ==========================================

@app.route("/admin/add-candidate", methods=["POST"])
def add_candidate():

    name = request.form.get("name")
    party = request.form.get("party")

    if not name or not party:
        return "Candidate name and party are required!"

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            INSERT INTO candidates (name, party)
            VALUES (%s, %s)
            """,
            (name, party)
        )

        conn.commit()

    except Exception as e:

        conn.rollback()

        cur.close()
        conn.close()

        return f"Add Candidate Error: {e}"

    cur.close()
    conn.close()

    return redirect(url_for("admin"))


# ==========================================
# SAFE DELETE CANDIDATE
# ==========================================

@app.route(
    "/admin/delete-candidate/<int:candidate_id>",
    methods=["POST"]
)
def delete_candidate(candidate_id):

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        cur.execute(
            """
            SELECT COUNT(*)
            FROM votes
            WHERE candidate_id = %s
            """,
            (candidate_id,)
        )

        vote_count = cur.fetchone()[0]

        if vote_count > 0:

            cur.close()
            conn.close()

            return (
                f"Cannot delete candidate. "
                f"{vote_count} vote(s) already recorded."
            )

        cur.execute(
            """
            DELETE FROM candidates
            WHERE id = %s
            """,
            (candidate_id,)
        )

        conn.commit()

    except Exception as e:

        conn.rollback()

        cur.close()
        conn.close()

        return f"Delete Candidate Error: {e}"

    cur.close()
    conn.close()

    return redirect(url_for("admin"))


# ==========================================
# LOGOUT
# ==========================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("index"))


# ==========================================
# RUN FLASK APPLICATION
# ==========================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
