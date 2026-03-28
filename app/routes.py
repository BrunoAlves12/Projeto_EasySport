import os
import random
from datetime import datetime, timedelta

from flask import Blueprint, current_app, redirect, render_template, url_for, flash, request, session

from app.models import EstadoUser, User, Reserva, Espaco, Pagamento
from app.extensions import db

main_bp = Blueprint("main", __name__)


def _espacos_homepage():
    espacos = Espaco.query.filter_by(ativo=True).all()
    quantidade = min(3, len(espacos))

    if quantidade == 0:
        return [], False

    espacos_destaque = random.sample(espacos, quantidade)

    for espaco in espacos_destaque:
        imagem = espaco.imagem or current_app.config["ESPACO_IMAGEM_DEFAULT"]
        caminho_imagem = os.path.join(current_app.static_folder, imagem.replace("/", os.sep))

        espaco.imagem_homepage = imagem if os.path.exists(caminho_imagem) else current_app.config["ESPACO_IMAGEM_DEFAULT"]
        espaco.modalidade_homepage = (espaco.modalidade or "Espaço desportivo").strip()
        espaco.descricao_curta = (espaco.descricao or "Espaço pronto para reserva.").strip()

    return espacos_destaque, len(espacos) > quantidade


def _get_current_user():
    if not session.get("user_id"):
        return None

    return User.query.get(session["user_id"])


def _render_editar_utilizador_form(user, form_data=None):
    return render_template("editar_utilizador.html", user=user, form_data=form_data or {})


@main_bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        return redirect(url_for("main.index"))

    if session.get("user_id"):
        if session.get("is_admin"):
            return redirect(url_for("main.admin_dashboard"))

        return redirect(url_for("main.espacos_homepage"))

    return render_template("landing.html")


@main_bp.route("/espacos")
def espacos_homepage():
    if session.get("is_admin"):
        return redirect(url_for("main.admin_dashboard"))

    current_user = _get_current_user()
    espacos_destaque, mostrar_botao_mais_espacos = _espacos_homepage()

    return render_template(
        "index.html",
        espacos_destaque=espacos_destaque,
        mostrar_botao_mais_espacos=mostrar_botao_mais_espacos,
        current_user=current_user
    )


@main_bp.route("/admin")
def admin_dashboard():
    if "user_id" not in session:
        flash("Tem de fazer login primeiro", "danger")
        return redirect(url_for("auth.login_page"))

    if not session.get("is_admin"):
        flash("Acesso restrito ao administrador", "danger")
        return redirect(url_for("main.index"))

    current_user = _get_current_user()
    now = datetime.now()
    inicio_hoje = datetime(now.year, now.month, now.day)
    inicio_amanha = inicio_hoje + timedelta(days=1)

    reservas_hoje = Reserva.query.filter(
        Reserva.dataInicio >= inicio_hoje,
        Reserva.dataInicio < inicio_amanha
    ).count()

    utilizadores_recentes = User.query.filter_by(isAdmin=False).order_by(User.id.desc()).limit(3).all()
    espacos_ativos = Espaco.query.filter_by(ativo=True).count()
    pagamentos_pendentes = Pagamento.query.filter_by(estado="pendente").count()

    recent_names = ", ".join(user.nome for user in reversed(utilizadores_recentes))
    if not recent_names:
        recent_names = "Sem novos registos recentes"

    summary_cards = [
        {
            "titulo": "Reservas para hoje",
            "valor": reservas_hoje,
            "detalhe": "Reservas com início marcado para hoje.",
            "icone": "calendar",
        },
        {
            "titulo": "Utilizadores recentes",
            "valor": len(utilizadores_recentes),
            "detalhe": recent_names,
            "icone": "users",
        },
        {
            "titulo": "Espaços ativos",
            "valor": espacos_ativos,
            "detalhe": "Espaços atualmente disponíveis na plataforma.",
            "icone": "spaces",
        },
        {
            "titulo": "Pagamentos pendentes",
            "valor": pagamentos_pendentes,
            "detalhe": "Pagamentos ainda por regularizar.",
            "icone": "payments",
        },
    ]

    admin_links = [
        {
            "titulo": "Gerir utilizadores",
            "texto": "Consulta, edita e organiza os utilizadores registados na plataforma.",
            "rota": url_for("main.listar_utilizadores"),
            "botao": "Abrir utilizadores",
            "icone": "users",
        },
        {
            "titulo": "Gerir espaços",
            "texto": "Adiciona novos espaços e controla a disponibilidade dos espaços existentes.",
            "rota": url_for("main.listar_espacos_page"),
            "botao": "Abrir espaços",
            "icone": "spaces",
        },
        {
            "titulo": "Consultar reservas",
            "texto": "Acompanha todas as reservas e confirma rapidamente o estado de cada pedido.",
            "rota": url_for("reservas.listar_reservas"),
            "botao": "Ver reservas",
            "icone": "calendar",
        },
        {
            "titulo": "Consultar pagamentos",
            "texto": "Revê pagamentos associados às reservas e acompanha o estado financeiro.",
            "rota": url_for("pagamentos.listar_pagamentos"),
            "botao": "Ver pagamentos",
            "icone": "payments",
        },
    ]

    return render_template(
        "admin.html",
        current_user=current_user,
        summary_cards=summary_cards,
        admin_links=admin_links
    )


@main_bp.route("/registar-page")
def registar_page():
    return render_template("registar.html", form_data={})


@main_bp.route("/espaco-page")
def espaco_page():
    if "user_id" not in session:
        flash("Tem de fazer login primeiro", "danger")
        return redirect(url_for("auth.login_page"))

    if not session.get("is_admin"):
        flash("Acesso restrito ao administrador", "danger")
        return redirect(url_for("main.index"))

    return render_template("espaco.html", form_data={})


@main_bp.route("/listar-espacos")
def listar_espacos_page():
    return redirect(url_for("espaco.listar_espacos"))


@main_bp.route("/listar-utilizadores")
def listar_utilizadores():
    if "user_id" not in session:
        flash("Tem de fazer login primeiro", "danger")
        return redirect(url_for("auth.login_page"))

    if not session.get("is_admin"):
        flash("Acesso restrito ao administrador", "danger")
        return redirect(url_for("main.index"))

    users = User.query.filter_by(isAdmin=False).all()

    return render_template("listar_utilizadores.html", users=users)


@main_bp.route("/remover-utilizador/<int:user_id>", methods=["POST"])
def remover_utilizador(user_id):
    if "user_id" not in session:
        flash("Tem de fazer login primeiro", "danger")
        return redirect(url_for("auth.login_page"))

    if not session.get("is_admin"):
        flash("Acesso restrito ao administrador", "danger")
        return redirect(url_for("main.index"))

    user = User.query.get_or_404(user_id)

    db.session.delete(user)
    db.session.commit()

    flash("Utilizador removido com sucesso!", "success")

    return redirect(url_for("main.listar_utilizadores"))


@main_bp.route("/perfil-utilizador")
def perfil_utilizador():
    if "user_id" not in session:
        flash("Tem de fazer login", "danger")
        return redirect(url_for("auth.login_page"))

    user = User.query.get(session["user_id"])

    return _render_editar_utilizador_form(user)


@main_bp.route("/editar-utilizador/<int:user_id>")
def editar_utilizador_page(user_id):
    if "user_id" not in session:
        flash("Tem de fazer login primeiro", "danger")
        return redirect(url_for("auth.login_page"))

    if not session.get("is_admin"):
        flash("Acesso restrito ao administrador", "danger")
        return redirect(url_for("main.index"))

    user = User.query.get_or_404(user_id)

    return _render_editar_utilizador_form(user)


@main_bp.route("/editar-utilizador/<int:user_id>", methods=["POST"])
def editar_utilizador(user_id):
    if "user_id" not in session:
        flash("Tem de fazer login primeiro", "danger")
        return redirect(url_for("auth.login_page"))

    user = User.query.get_or_404(user_id)

    if not session.get("is_admin") and session["user_id"] != user_id:
        flash("Acesso restrito", "danger")
        return redirect(url_for("main.index"))

    nome = request.form.get("nome", "").strip()
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    estado = request.form.get("estado", "").strip()
    form_data = {
        "nome": nome,
        "username": username,
        "email": email,
        "estado": estado,
    }

    if not nome or not username or not email or not estado:
        flash("Todos os campos são obrigatórios", "danger")
        return _render_editar_utilizador_form(user, form_data)

    existe_username = User.query.filter(
        User.username == username,
        User.id != user.id
    ).first()

    if existe_username:
        flash("Username já existe", "danger")
        return _render_editar_utilizador_form(user, form_data)

    existe_email = User.query.filter(
        User.email == email,
        User.id != user.id
    ).first()

    if existe_email:
        flash("Email já existe", "danger")
        return _render_editar_utilizador_form(user, form_data)

    user.nome = nome
    user.username = username
    user.email = email

    if estado == "ativo":
        user.estado = EstadoUser.ativo
    else:
        user.estado = EstadoUser.inativo

    db.session.commit()

    if not session.get("is_admin") and session["user_id"] == user.id and user.estado == EstadoUser.inativo:
        session.clear()
        flash("Conta desativada com sucesso.", "success")
        return redirect(url_for("main.index"))

    flash("Utilizador atualizado com sucesso!", "success")

    if session.get("is_admin"):
        return redirect(url_for("main.listar_utilizadores"))

    return redirect(url_for("main.index"))


@main_bp.route("/reservar-page")
def reservar_page():
    if "user_id" not in session:
        flash("Tem de fazer login primeiro", "danger")
        return redirect(url_for("auth.login_page"))

    return render_template("reservar.html")
