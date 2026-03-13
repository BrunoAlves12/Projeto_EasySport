from flask import Blueprint, request, redirect, url_for, flash, session, render_template
from app.models import Espaco
from app.extensions import db

espaco_bp = Blueprint("espaco", __name__)


@espaco_bp.route("/espaco", methods=["POST"])
def criar_espaco():

    nome = request.form["nome"]
    descricao = request.form["descricao"]
    preco_str = float(request.form["preco"])

    try:
        preco = float(preco_str)
    except:
        flash("Preço inválido")
        return redirect(url_for("main.espaco_page"))

    # validações
    if not nome:
        flash("Nome do espaço é obrigatório")
        return redirect(url_for("main.espaco_page"))

    if preco <= 0:
        flash("Preço Inválido!")
        return redirect(url_for("main.espaco_page"))
    
    if not session.get("is_admin"):
        flash("Acesso restrito ao admin")
        return redirect(url_for("main.index"))

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
    
    if session.get("is_admin"):
        espacos = Espaco.query.all()
    else:
        espacos = Espaco.query.filter_by(ativo=True).all()

    return render_template("listar_espacos.html", espacos=espacos)

@espaco_bp.route("/editar-espaco/<int:id>", methods=["GET", "POST"])
def editar_espaco(id):

    if not session.get("is_admin"):
        flash("Acesso restrito ao admin")
        return redirect(url_for("main.index"))

    espaco = Espaco.query.get(id)

    if not espaco:
        flash("Espaço não encontrado")
        return redirect(url_for("main.index"))

    if request.method == "POST":
        nome = request.form["nome"]
        descricao = request.form["descricao"]
        preco_str = request.form["preco"]

        if not nome:
            flash("Nome do espaço é obrigatório")
            return redirect(url_for("espaco.editar_espaco", id=id))

        try:
            preco = float(preco_str)
        except:
            flash("Preço inválido")
            return redirect(url_for("espaco.editar_espaco", id=id))

        if preco <= 0:
            flash("Preço inválido")
            return redirect(url_for("espaco.editar_espaco", id=id))

        espaco.nome = nome
        espaco.descricao = descricao
        espaco.precoHora = preco

        db.session.commit()
        flash("Espaço editado com sucesso")
        return redirect(url_for("espaco.listar_espacos"))

    return render_template("editar_espaco.html", espaco=espaco)


@espaco_bp.route("/desativar-espaco/<int:id>")
def desativar_espaco(id):

    if not session.get("is_admin"):
        flash("Acesso restrito ao admin")
        return redirect(url_for("main.index"))

    espaco = Espaco.query.get(id)

    if not espaco:
        flash("Espaço não encontrado")
        return redirect(url_for("main.index"))

    espaco.ativo = False
    db.session.commit()

    flash("Espaço desativado com sucesso")
    return redirect(url_for("espaco.listar_espacos"))


@espaco_bp.route("/ativar-espaco/<int:id>")
def ativar_espaco(id):

    if not session.get("is_admin"):
        flash("Acesso restrito ao admin")
        return redirect(url_for("main.index"))

    espaco = Espaco.query.get(id)

    if not espaco:
        flash("Espaço não encontrado")
        return redirect(url_for("main.index"))

    espaco.ativo = True
    db.session.commit()

    flash("Espaço ativado com sucesso")
    return redirect(url_for("espaco.listar_espacos"))