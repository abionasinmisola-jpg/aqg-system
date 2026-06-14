from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from datetime import datetime, timedelta
from functools import wraps
from backend import db, limiter
from backend.models.user import User
from backend.utils.forms import LecturerLoginForm, LecturerFirstLoginForm

lecturer_bp = Blueprint("lecturer", __name__, url_prefix="/lecturer-portal")

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


def lecturer_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_lecturer():
            flash("Access denied.", "danger")
            return redirect(url_for("lecturer.login"))
        return f(*args, **kwargs)
    return decorated


@lecturer_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated and current_user.is_lecturer():
        return redirect(url_for("lecturer.dashboard"))

    form = LecturerLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(
            email=form.email.data.lower(),
            role="lecturer"
        ).first()

        # Check if account is locked
        if user and user.locked_until:
            if datetime.utcnow() < user.locked_until:
                remaining = int((user.locked_until - datetime.utcnow()).total_seconds() // 60)
                flash(f"Account locked. Try again in {remaining} minute(s).", "danger")
                return render_template("lecturer/login.html", form=form)
            else:
                user.failed_logins = 0
                user.locked_until = None
                db.session.commit()

        if user and user.check_password(form.password.data):
            user.failed_logins = 0
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user)
            flash(f"Welcome, {user.full_name}!", "success")

            # Force password change on first login
            if user.must_change_password:
                return redirect(url_for("lecturer.change_password"))
            return redirect(url_for("lecturer.dashboard"))
        else:
            if user:
                user.failed_logins += 1
                if user.failed_logins >= MAX_FAILED_ATTEMPTS:
                    user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
                    flash(f"Too many failed attempts. Account locked for {LOCKOUT_MINUTES} minutes.", "danger")
                else:
                    remaining = MAX_FAILED_ATTEMPTS - user.failed_logins
                    flash(f"Invalid credentials. {remaining} attempt(s) remaining.", "danger")
                db.session.commit()
            else:
                flash("Invalid email or password.", "danger")

    return render_template("lecturer/login.html", form=form)


@lecturer_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if not current_user.is_lecturer():
        return redirect(url_for("lecturer.login"))

    form = LecturerFirstLoginForm()
    if form.validate_on_submit():
        current_user.set_password(form.new_password.data)
        current_user.must_change_password = False
        db.session.commit()
        flash("Password changed successfully! Welcome to AQG.", "success")
        return redirect(url_for("lecturer.dashboard"))

    return render_template("lecturer/change_password.html", form=form)


@lecturer_bp.route("/dashboard")
@login_required
@lecturer_required
def dashboard():
    return render_template("lecturer/dashboard.html", user=current_user)


@lecturer_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("lecturer.login"))