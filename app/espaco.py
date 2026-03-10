from flask import Blueprint, request, redirect, url_for, flash
from app.models import Espaco
from app.extensions import db

espaco_bp = Blueprint("espaco", __name__)


@espaco_bp.route("/espaco", methods=["POST"])
def criar_espaco():

    nome = request.form["nome"]
    descricao = request.form["descricao"]
    preco = float(request.form["preco"])


    # validações
    if not nome:
        flash("Nome do espaço é obrigatório")
        return redirect(url_for("main.espaco_page"))

    if preco <= 0:
        flash("Preço Inválido!")
        return redirect(url_for("main.espaco_page"))

    espaco = Espaco(
        nome=nome, 
        descricao=descricao, 
        precoHora=preco,
        ativo=True
    )

    db.session.add(espaco)
    db.session.commit()

    flash("Espaço criado com sucesso!")

    return redirect(url_for("main.index"))


@espaco_bp.route("/espaco", methods=["GET"])
def listar_espacos():
    
    espacos = Espaco.query.all()

    resultado = []  
    for e in espacos:
        resultado.append({
            "id": e.id,
            "nome": e.nome,
            "descricao": e.descricao,
            "preco": e.precoHora,
            "ativo": e.ativo
        })
    return resultado 