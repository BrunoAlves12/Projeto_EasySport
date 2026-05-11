from app import create_app
from app.auth import _hash_password, migrar_passwords_antigas
from app.extensions import db
from app.models import User

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        admin = User.query.filter_by(isAdmin=True).first()

        if not admin:
            admin = User(
                nome="Admin",
                email="admin@example.com",
                username="admin",
                password=_hash_password("Admin123!"),
                isAdmin=True,
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin criado automaticamente")

        total_migradas = migrar_passwords_antigas()
        if total_migradas:
            print(f"Passwords antigas migradas para hash: {total_migradas}")

    app.run(debug=True)
