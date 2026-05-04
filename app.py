
from flask import Flask, render_template, request, redirect, url_for, session, abort
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import init_db, email_exists, create_user, get_user_by_email, get_user_by_id, get_user_stats, get_recent_expenses, get_expenses_by_category

app = Flask(__name__)
app.secret_key = "dev-secret-change-in-production"


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("landing"))
    if request.method == "GET":
        return render_template("register.html")

    name     = request.form.get("name", "").strip()
    email    = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not name:
        return render_template("register.html", error="Name is required.", name=name, email=email)
    if not email:
        return render_template("register.html", error="Email is required.", name=name, email=email)
    if len(password) < 8:
        return render_template("register.html", error="Password must be at least 8 characters.", name=name, email=email)
    if email_exists(email):
        return render_template("register.html", error="An account with that email already exists.", name=name, email=email)

    create_user(name, email, generate_password_hash(password))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("landing"))
    if request.method == "GET":
        return render_template("login.html")

    email    = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not email:
        return render_template("login.html", error="Email is required.", email=email)
    if not password:
        return render_template("login.html", error="Password is required.", email=email)

    user = get_user_by_email(email)
    if user is None or not check_password_hash(user["password_hash"], password):
        return render_template("login.html", error="Invalid email or password.", email=email)

    session.clear()
    session["user_id"] = user["id"]
    return redirect(url_for("landing"))


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    uid = session["user_id"]
    user = get_user_by_id(uid)
    if user is None:
        abort(404)
    dt = datetime.strptime(user["created_at"][:10], "%Y-%m-%d")
    member_since = dt.strftime("%d %b %Y")
    stats = get_user_stats(uid)
    raw_recent = get_recent_expenses(uid)
    recent = [
        {
            "date": datetime.strptime(r["date"], "%Y-%m-%d").strftime("%d %b %Y"),
            "description": r["description"],
            "amount": r["amount"],
            "category": r["category"],
        }
        for r in raw_recent
    ]
    by_category = get_expenses_by_category(uid)
    max_cat_amount = by_category[0]["total"] if by_category else 1
    return render_template(
        "profile.html",
        user=user,
        member_since=member_since,
        stats=stats,
        recent=recent,
        by_category=by_category,
        max_cat_amount=max_cat_amount,
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5001)
