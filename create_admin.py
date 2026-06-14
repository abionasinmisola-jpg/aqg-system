from backend import create_app, db, bcrypt
from backend.models.user import User

app = create_app()

with app.app_context():
    # Check if admin already exists
    existing = User.query.filter_by(role="admin").first()
    if existing:
        print("Admin account already exists!")
    else:
        admin = User(
            full_name="Super Admin",
            email="aqgsystem@gmail.com",
            role="admin"
        )
        admin.set_password("Admin@12345")
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin account created successfully!")
        print("Email:    admin@aqgsystem.com")
        print("Password: Admin@12345")
        print("⚠️  Please change this password after first login!")