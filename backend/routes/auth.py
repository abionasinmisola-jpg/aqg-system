from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from backend import db
from backend.models.user import User
from backend.utils.forms import StudentLoginForm, StudentRegisterForm

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated and current_user.is_student():
        return redirect(url_for("student_views.dashboard"))

    form = StudentRegisterForm()
    if form.validate_on_submit():
        user = User(
            full_name=form.full_name.data.strip(),
            email=form.email.data.lower().strip(),
            matric_no=form.matric_no.data.upper().strip(),
            role="student"
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Account created! Please log in.", "success")
        return redirect(url_for("auth.student_login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def student_login():
    if current_user.is_authenticated and current_user.is_student():
        return redirect(url_for("student_views.dashboard"))

    form = StudentLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(
            email=form.email.data.lower(),
            role="student"
        ).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash(f"Welcome back, {user.full_name}!", "success")
            return redirect(url_for("student_views.dashboard"))
        else:
            flash("Invalid email or password.", "danger")

    return render_template("auth/student_login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.student_login"))