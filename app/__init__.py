import os
from flask import Flask

from .extensions import db

def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///easycourt.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["ESPACO_IMAGEM_DEFAULT"] = "img/easysport-logo.png"
    app.config["ESPACOS_IMG_UPLOAD_FOLDER"] = os.path.join(app.static_folder, "img", "espacos")

    db.init_app(app)
    os.makedirs(app.config["ESPACOS_IMG_UPLOAD_FOLDER"], exist_ok=True)

    from .auth import auth_bp
    from .reservas import reservas_bp
    from .pagamentos import pagamentos_bp
    from .routes import main_bp
    from .espaco import espaco_bp

   
    app.register_blueprint(auth_bp)
    app.register_blueprint(reservas_bp)
    app.register_blueprint(pagamentos_bp)
    app.register_blueprint(espaco_bp)
    app.register_blueprint(main_bp)
    
    return app
