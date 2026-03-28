import os
import uuid

from flask import Blueprint, current_app, request, redirect, url_for, flash, session, render_template
from werkzeug.utils import secure_filename

from app.models import Espaco
from app.extensions import db

espaco_bp = Blueprint("espaco", __name__)

EXTENSOES_IMAGEM_PERMITIDAS = {"png", "jpg", "jpeg", "gif", "webp"}


def _guardar_imagem_espaco(imagem_file):
    if not imagem_file or not imagem_file.filename:
        return current_app.config["ESPACO_IMAGEM_DEFAULT"]

    nome_seguro = secure_filename(imagem_file.filename)
    extensao = nome_seguro.rsplit(".", 1)[-1].lower() if "." in nome_seguro else ""

    if extensao not in EXTENSOES_IMAGEM_PERMITIDAS:
        return None

    nome_unico = f"{uuid.uuid4().hex}.{extensao}"
    pasta_upload = current_app.config["ESPACOS_IMG_UPLOAD_FOLDER"]
    caminho_ficheiro = os.path.join(pasta_upload, nome_unico)

    imagem_file.save(caminho_ficheiro)
    return f"img/espacos/{nome_unico}"


def _obter_imagem_para_espaco(imagem_file, imagem_atual=None):
    if not imagem_file or not imagem_file.filename:
        if imagem_atual:
            return imagem_atual

        return current_app.config["ESPACO_IMAGEM_DEFAULT"]

    return _guardar_imagem_espaco(imagem_file)


def _resolver_imagem_listagem(espaco):
    imagem = espaco.imagem or current_app.config["ESPACO_IMAGEM_DEFAULT"]
    caminho_imagem = os.path.join(current_app.static_folder, imagem.replace("/", os.sep))

    if not os.path.exists(caminho_imagem):
        return current_app.config["ESPACO_IMAGEM_DEFAULT"]

    return imagem


def _render_criar_espaco_form(form_data=None):
    return render_template("espaco.html", form_data=form_data or {})


def _render_editar_espaco_form(espaco, form_data=None):
    espaco.imagem_listagem = _resolver_imagem_listagem(espaco)
    return render_template("editar_espaco.html", espaco=espaco, form_data=form_data or {})


@espaco_bp.route("/espaco", methods=["POST"])
def criar_espaco():
    nome = request.form.get("nome", "").strip()
    modalidade = request.form.get("modalidade", "").strip()
    descricao = request.form.get("descricao", "").strip()
    preco_str = request.form.get("preco", "").strip()
    imagem_file = request.files.get("imagem")

    form_data = {
        "nome": nome,
        "modalidade": modalidade,
        "descricao": descricao,
        "preco": preco_str,
    }

    try:
        preco = float(preco_str)
    except Exception:
        flash("Preço inválido", "danger")
        return _render_criar_espaco_form(form_data)

    if not nome:
        flash("Nome do espaço é obrigatório", "danger")
        return _render_criar_espaco_form(form_data)

    if not modalidade:
        flash("Modalidade é obrigatória", "danger")
        return _render_criar_espaco_form(form_data)

    if preco <= 0:
        flash("Preço inválido", "danger")
        return _render_criar_espaco_form(form_data)

    if not session.get("is_admin"):
        flash("Acesso restrito ao admin", "danger")
        return redirect(url_for("main.index"))

    imagem = _obter_imagem_para_espaco(imagem_file)
    if imagem_file and imagem is None:
        flash("Formato de imagem inválido", "danger")
        return _render_criar_espaco_form(form_data)

    espaco = Espaco(
        nome=nome,
        modalidade=modalidade,
        descricao=descricao,
        imagem=imagem,
        precoHora=preco,
        ativo=True,
    )

    db.session.add(espaco)
    db.session.commit()

    flash("Espaço criado com sucesso!", "success")
    return redirect(url_for("espaco.listar_espacos"))


@espaco_bp.route("/espaco", methods=["GET"])
def listar_espacos():
    if session.get("is_admin"):
        espacos = Espaco.query.all()
    else:
        espacos = Espaco.query.filter_by(ativo=True).all()

    for espaco in espacos:
        espaco.imagem_listagem = _resolver_imagem_listagem(espaco)
        espaco.modalidade_listagem = (espaco.modalidade or "Espaço desportivo").strip()

    return render_template("listar_espacos.html", espacos=espacos)


@espaco_bp.route("/editar-espaco/<int:id>", methods=["GET", "POST"])
def editar_espaco(id):
    if not session.get("is_admin"):
        flash("Acesso restrito ao admin", "danger")
        return redirect(url_for("main.index"))

    espaco = Espaco.query.get(id)

    if not espaco:
        flash("Espaço não encontrado", "danger")
        return redirect(url_for("main.index"))

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        modalidade = request.form.get("modalidade", "").strip()
        descricao = request.form.get("descricao", "").strip()
        preco_str = request.form.get("preco", "").strip()
        imagem_file = request.files.get("imagem")

        form_data = {
            "nome": nome,
            "modalidade": modalidade,
            "descricao": descricao,
            "preco": preco_str,
        }

        if not nome:
            flash("Nome do espaço é obrigatório", "danger")
            return _render_editar_espaco_form(espaco, form_data)

        if not modalidade:
            flash("Modalidade é obrigatória", "danger")
            return _render_editar_espaco_form(espaco, form_data)

        try:
            preco = float(preco_str)
        except Exception:
            flash("Preço inválido", "danger")
            return _render_editar_espaco_form(espaco, form_data)

        if preco <= 0:
            flash("Preço inválido", "danger")
            return _render_editar_espaco_form(espaco, form_data)

        imagem = _obter_imagem_para_espaco(imagem_file, espaco.imagem)
        if imagem_file and imagem is None:
            flash("Formato de imagem inválido", "danger")
            return _render_editar_espaco_form(espaco, form_data)

        espaco.nome = nome
        espaco.modalidade = modalidade
        espaco.descricao = descricao
        espaco.imagem = imagem
        espaco.precoHora = preco

        db.session.commit()
        flash("Espaço editado com sucesso", "success")
        return redirect(url_for("espaco.listar_espacos"))

    return _render_editar_espaco_form(espaco)


@espaco_bp.route("/desativar-espaco/<int:id>")
def desativar_espaco(id):
    if not session.get("is_admin"):
        flash("Acesso restrito ao admin", "danger")
        return redirect(url_for("main.index"))

    espaco = Espaco.query.get(id)

    if not espaco:
        flash("Espaço não encontrado", "danger")
        return redirect(url_for("main.index"))

    espaco.ativo = False
    db.session.commit()

    flash("Espaço desativado com sucesso", "success")
    return redirect(url_for("espaco.listar_espacos"))


@espaco_bp.route("/ativar-espaco/<int:id>")
def ativar_espaco(id):
    if not session.get("is_admin"):
        flash("Acesso restrito ao admin", "danger")
        return redirect(url_for("main.index"))

    espaco = Espaco.query.get(id)

    if not espaco:
        flash("Espaço não encontrado", "danger")
        return redirect(url_for("main.index"))

    espaco.ativo = True
    db.session.commit()

    flash("Espaço ativado com sucesso", "success")
    return redirect(url_for("espaco.listar_espacos"))
