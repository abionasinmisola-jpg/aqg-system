from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from backend.models.user import User


# ── Student Forms ─────────────────────────────────────────────
class StudentRegisterForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=120)])
    matric_no = StringField("Matric Number", validators=[DataRequired(), Length(min=3, max=50)])
    email     = StringField("Email", validators=[DataRequired(), Email(), Length(max=150)])
    password  = PasswordField("Password", validators=[
        DataRequired(),
        Length(min=8, message="Password must be at least 8 characters")
    ])
    confirm   = PasswordField("Confirm Password", validators=[
        DataRequired(),
        EqualTo("password", message="Passwords must match")
    ])
    submit    = SubmitField("Create Account")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError("An account with that email already exists.")


class StudentLoginForm(FlaskForm):
    email    = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit   = SubmitField("Log In")


# ── Lecturer Forms ────────────────────────────────────────────
class LecturerLoginForm(FlaskForm):
    email    = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit   = SubmitField("Sign In")


class LecturerFirstLoginForm(FlaskForm):
    new_password = PasswordField("New Password", validators=[
        DataRequired(),
        Length(min=8, message="Password must be at least 8 characters")
    ])
    confirm = PasswordField("Confirm Password", validators=[
        DataRequired(),
        EqualTo("new_password", message="Passwords must match")
    ])
    submit = SubmitField("Set New Password")


# ── Admin Forms ───────────────────────────────────────────────
class AdminLoginForm(FlaskForm):
    email    = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit   = SubmitField("Sign In")


class CreateLecturerForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=120)])
    email     = StringField("Email", validators=[DataRequired(), Email(), Length(max=150)])
    submit    = SubmitField("Create Lecturer Account")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError("An account with that email already exists.")