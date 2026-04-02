from app import create_app
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
                password="admin",
                isAdmin=True,
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin criado automaticamente")

    app.run(debug=True)
