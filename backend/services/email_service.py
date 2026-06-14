import os
import random
import string
from flask import current_app
from flask_mail import Mail, Message

mail = Mail()


def init_mail(app):
    """Initialize Flask-Mail with app config"""
    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_EMAIL")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_EMAIL")
    mail.init_app(app)


def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))


def send_lecturer_credentials(lecturer_name, lecturer_email, temp_password, login_url):
    """
    Send lecturer account credentials when admin creates their account
    """
    try:
        msg = Message(
            subject="Your AQG System Lecturer Account",
            recipients=[lecturer_email]
        )
        msg.html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #0d1f3c; padding: 20px; border-radius: 10px 10px 0 0; text-align: center;">
                <h1 style="color: #e8a020; margin: 0; font-size: 24px;">AQG System</h1>
                <p style="color: rgba(255,255,255,0.6); margin: 5px 0 0;">Automated Question Generation</p>
            </div>
            <div style="background: #fff; padding: 30px; border: 1px solid #e2e8f0; border-top: none;">
                <h2 style="color: #0d1f3c; margin-top: 0;">Welcome, {lecturer_name}!</h2>
                <p style="color: #64748b; line-height: 1.6;">
                    Your lecturer account has been created on the AQG System.
                    Please use the credentials below to log in.
                </p>

                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin: 20px 0;">
                    <p style="margin: 0 0 10px; color: #64748b; font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">Your Login Credentials</p>
                    <p style="margin: 0 0 8px; color: #1e293b;"><strong>Email:</strong> {lecturer_email}</p>
                    <p style="margin: 0 0 8px; color: #1e293b;"><strong>Temporary Password:</strong>
                        <span style="background: #0d1f3c; color: #e8a020; padding: 4px 12px; border-radius: 6px; font-family: monospace; font-size: 16px; font-weight: 700;">{temp_password}</span>
                    </p>
                    <p style="margin: 0; color: #1e293b;"><strong>Login URL:</strong>
                        <a href="{login_url}" style="color: #2563eb;">{login_url}</a>
                    </p>
                </div>

                <div style="background: #fef3c7; border: 1px solid #fde68a; border-radius: 8px; padding: 14px; margin: 20px 0;">
                    <p style="margin: 0; color: #92400e; font-size: 13px;">
                        ⚠️ <strong>Important:</strong> You will be required to change this temporary password on your first login.
                        Please keep your credentials secure and do not share them with anyone.
                    </p>
                </div>

                <a href="{login_url}" style="display: inline-block; background: #0d1f3c; color: #fff; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 700; margin-top: 10px;">
                    Login to AQG System →
                </a>
            </div>
            <div style="background: #f8fafc; padding: 16px; border-radius: 0 0 10px 10px; text-align: center; border: 1px solid #e2e8f0; border-top: none;">
                <p style="margin: 0; color: #94a3b8; font-size: 12px;">
                    This email was sent by the AQG System Administrator.
                    If you did not expect this email, please ignore it.
                </p>
            </div>
        </div>
        """
        mail.send(msg)
        return {"success": True, "message": "Credentials sent successfully"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def send_otp_email(lecturer_name, lecturer_email, otp):
    """
    Send OTP for password reset
    """
    try:
        msg = Message(
    subject="Your AQG System Lecturer Account",
    recipients=[lecturer_email],
    reply_to=os.getenv("MAIL_EMAIL")
        )
        msg.html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #0d1f3c; padding: 20px; border-radius: 10px 10px 0 0; text-align: center;">
                <h1 style="color: #e8a020; margin: 0; font-size: 24px;">AQG System</h1>
                <p style="color: rgba(255,255,255,0.6); margin: 5px 0 0;">Password Reset</p>
            </div>
            <div style="background: #fff; padding: 30px; border: 1px solid #e2e8f0; border-top: none;">
                <h2 style="color: #0d1f3c; margin-top: 0;">Password Reset Request</h2>
                <p style="color: #64748b; line-height: 1.6;">
                    Hi {lecturer_name}, we received a request to reset your password.
                    Use the OTP below to proceed.
                </p>

                <div style="text-align: center; margin: 30px 0;">
                    <div style="background: #0d1f3c; color: #e8a020; font-size: 36px; font-weight: 900; letter-spacing: 12px; padding: 20px 30px; border-radius: 12px; display: inline-block; font-family: monospace;">
                        {otp}
                    </div>
                    <p style="color: #94a3b8; font-size: 13px; margin-top: 12px;">
                        This OTP expires in <strong>10 minutes</strong>
                    </p>
                </div>

                <div style="background: #fee2e2; border: 1px solid #fecaca; border-radius: 8px; padding: 14px;">
                    <p style="margin: 0; color: #991b1b; font-size: 13px;">
                        🔒 If you did not request a password reset, please ignore this email
                        and ensure your account is secure.
                    </p>
                </div>
            </div>
            <div style="background: #f8fafc; padding: 16px; border-radius: 0 0 10px 10px; text-align: center; border: 1px solid #e2e8f0; border-top: none;">
                <p style="margin: 0; color: #94a3b8; font-size: 12px;">
                    This is an automated email from the AQG System. Do not reply.
                </p>
            </div>
        </div>
        """
        mail.send(msg)
        return {"success": True, "message": "OTP sent successfully"}
    except Exception as e:
        return {"success": False, "message": str(e)}