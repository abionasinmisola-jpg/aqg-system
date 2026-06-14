from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from functools import wraps

student_bp = Blueprint("student", __name__)


def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_student():
            return redirect(url_for("auth.student_login"))
        return f(*args, **kwargs)
    return decorated


@student_bp.route("/dashboard")
@login_required
@student_required
def dashboard():
    return render_template("student/dashboard.html", user=current_user)