from flask import Blueprint, request
from app.models import Espaco
from app.extensions import db

espaco_bp = Blueprint("espaco", __name__)


@espaco_bp.route("/espacos", methods=["POST"])
def criar_espaco():

    nome = request.json["nome"]
    descricao = request.json["descricao"]
    preco = request.json["preco"]

    espaco = Espaco(
        nome=nome, 
        descricao=descricao, 
        precoHora=preco,
        ativo=True
    )

    db.session.add(espaco)
    db.session.commit()

    return {"mensagem": "Espaço criado com sucesso"}


@espaco_bp.route("/espacos", methods=["GET"])
def listar_espacos():
    
    espaco = Espaco.query.all()

    resultado = []  
    for e in espaco:
        resultado.append({
            "id": e.id,
            "nome": e.nome,
            "descricao": e.descricao,
            "preco": e.preco,
            "ativo": e.ativo
        })
    return resultado 