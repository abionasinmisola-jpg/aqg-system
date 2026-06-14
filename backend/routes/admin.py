from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from functools import wraps
from backend import db, limiter
from backend.models.user import User
from backend.utils.forms import AdminLoginForm, CreateLecturerForm
import secrets
import string

admin_bp = Blueprint("admin", __name__, url_prefix="/admin-portal")


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash("Access denied.", "danger")
            return redirect(url_for("admin.login"))
        return f(*args, **kwargs)
    return decorated


def generate_temp_password(length=10):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


@admin_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated and current_user.is_admin():
        return redirect(url_for("admin.dashboard"))

    form = AdminLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(
            email=form.email.data.lower(),
            role="admin"
        ).first()

        if user and user.check_password(form.password.data):
            login_user(user)
            flash(f"Welcome, {user.full_name}!", "success")
            return redirect(url_for("admin.dashboard"))
        else:
            flash("Invalid email or password.", "danger")

    return render_template("admin/login.html", form=form)


@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    lecturers = User.query.filter_by(role="lecturer").all()
    students  = User.query.filter_by(role="student").all()
    return render_template("admin/dashboard.html",
                           user=current_user,
                           lecturers=lecturers,
                           students=students)


@admin_bp.route("/create-lecturer", methods=["GET", "POST"])
@login_required
@admin_required
def create_lecturer():
    form = CreateLecturerForm()
    if form.validate_on_submit():
        temp_password = generate_temp_password()
        lecturer = User(
            full_name=form.full_name.data.strip(),
            email=form.email.data.lower().strip(),
            role="lecturer",
            must_change_password=True
        )
        lecturer.set_password(temp_password)
        db.session.add(lecturer)
        db.session.commit()

        # Send credentials via email
        from backend.services.email_service import send_lecturer_credentials
        login_url = "http://127.0.0.1:5000/lecturer-portal/login"
        email_result = send_lecturer_credentials(
            lecturer_name=lecturer.full_name,
            lecturer_email=lecturer.email,
            temp_password=temp_password,
            login_url=login_url
        )

        if email_result["success"]:
            flash(f"✅ Lecturer account created and credentials sent to {lecturer.email}!", "success")
        else:
            flash(f"✅ Account created! But email failed: {email_result['message']}. Temporary password: {temp_password}", "warning")

        return redirect(url_for("admin.dashboard"))

    return render_template("admin/create_lecturer.html", form=form)
    
@admin_bp.route("/delete-lecturer/<int:id>")
@login_required
@admin_required
def delete_lecturer(id):
    lecturer = User.query.get_or_404(id)
    if lecturer.role != "lecturer":
        flash("Invalid action.", "danger")
        return redirect(url_for("admin.dashboard"))
    db.session.delete(lecturer)
    db.session.commit()
    flash("Lecturer account deleted.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("admin.login"))