from flask import Flask
from .extensions import db

def create_app():
    app = Flask(__name__, template_folder="../templates")

    app.config["SECRET_KEY"] = "secret"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///easycourt.db"

    db.init_app(app)

    from .routes import routes
    from .utilizador.routes import rotas_utilizador
    from .reserva.routes import rotas_reserva

    app.register_blueprint(routes)
    app.register_blueprint(rotas_utilizador)
    app.register_blueprint(rotas_reserva)

    return app
