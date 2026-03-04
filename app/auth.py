from flask import Blueprint, request
from app.models import User
from app.extensions import db

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():

    nome = request.json["nome"]
    email = request.json["email"]
    password = request.json["password"]

    user = User(
        nome=nome, 
        email=email, 
        password=password
    )

    db.session.add(user)
    db.session.commit()

    return {"mensagem": "Utilizador criado com sucesso"}
