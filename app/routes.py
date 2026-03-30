import os
import random
from datetime import date, datetime, timedelta

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from app.auth import _validar_password
from app.extensions import db
from app.models import EstadoReserva, EstadoUser, Espaco, Pagamento, Reserva, User

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
        espaco.modalidade_homepage = (espaco.modalidade or "Espaco desportivo").strip()
        espaco.descricao_curta = (espaco.descricao or "Espaco pronto para reserva.").strip()

    return espacos_destaque, len(espacos) > quantidade


def _get_current_user():
    if not session.get("user_id"):
        return None

    return User.query.get(session["user_id"])


def _render_editar_utilizador_form(user, form_data=None):
    is_self_edit = session.get("user_id") == user.id
    is_admin_editing_other = session.get("is_admin") and not is_self_edit

    return render_template(
        "editar_utilizador.html",
        user=user,
        form_data=form_data or {},
        is_self_edit=is_self_edit,
        is_admin_editing_other=is_admin_editing_other,
    )


def _parse_data_nascimento(data_str):
    try:
        return datetime.strptime(data_str, "%Y-%m-%d").date()
    except ValueError:
        return None


def _email_e_valido(email):
    if "@" not in email:
        return False

    partes = email.split("@")
    return len(partes) == 2 and "." in partes[1]


def _normalizar_estado_utilizador(estado):
    return EstadoUser.ativo if estado == "ativo" else EstadoUser.inativo


def _obter_reservas_ativas_do_utilizador(user_id):
    agora = datetime.now()
    return Reserva.query.filter(
        Reserva.idUser == user_id,
        Reserva.dataFim >= agora,
        Reserva.estado.in_([EstadoReserva.pendente, EstadoReserva.confirmada]),
    ).all()


def _pode_inativar_conta(user):
    reservas_ativas = _obter_reservas_ativas_do_utilizador(user.id)
    reservas_confirmadas = [reserva for reserva in reservas_ativas if reserva.estado == EstadoReserva.confirmada]

    if reservas_confirmadas:
        return False, "Nao e possivel inativar a conta porque existem reservas confirmadas."

    reservas_pendentes = [reserva for reserva in reservas_ativas if reserva.estado == EstadoReserva.pendente]

    for reserva in reservas_pendentes:
        reserva.estado = EstadoReserva.cancelada
        pagamento = Pagamento.query.filter_by(idReserva=reserva.id).first()

        if pagamento and pagamento.estado != "pago":
            pagamento.estado = "cancelado"
            pagamento.dataPagamento = None

    return True, None


def _build_user_form_data(user, form_data):
    return {
        "nome": form_data.get("nome", user.nome),
        "username": form_data.get("username", user.username),
        "email": form_data.get("email", user.email),
        "dataNascimento": form_data.get(
            "dataNascimento",
            user.dataNascimento.isoformat() if user.dataNascimento else "",
        ),
        "estado": form_data.get("estado", user.estado.value),
    }


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
        current_user=current_user,
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
        Reserva.dataInicio < inicio_amanha,
    ).count()

    utilizadores_recentes = User.query.filter_by(isAdmin=False).order_by(User.id.desc()).limit(3).all()
    espacos_ativos = Espaco.query.filter_by(ativo=True).count()
    pagamentos_pendentes = Pagamento.query.join(
        Reserva,
        Pagamento.idReserva == Reserva.id,
    ).filter(
        Pagamento.estado == "pendente",
        Reserva.estado == EstadoReserva.pendente,
    ).count()

    recent_names = ", ".join(user.nome for user in reversed(utilizadores_recentes))
    if not recent_names:
        recent_names = "Sem novos registos recentes"

    summary_cards = [
        {
            "titulo": "Reservas para hoje",
            "valor": reservas_hoje,
            "detalhe": "Reservas com inicio marcado para hoje.",
            "icone": "calendar",
        },
        {
            "titulo": "Utilizadores recentes",
            "valor": len(utilizadores_recentes),
            "detalhe": recent_names,
            "icone": "users",
        },
        {
            "titulo": "Espacos ativos",
            "valor": espacos_ativos,
            "detalhe": "Espacos atualmente disponiveis na plataforma.",
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
            "titulo": "Gerir espacos",
            "texto": "Adiciona novos espacos e controla a disponibilidade dos espacos existentes.",
            "rota": url_for("main.listar_espacos_page"),
            "botao": "Abrir espacos",
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
            "texto": "Reve pagamentos associados as reservas e acompanha o estado financeiro.",
            "rota": url_for("pagamentos.listar_pagamentos"),
            "botao": "Ver pagamentos",
            "icone": "payments",
        },
    ]

    return render_template(
        "admin.html",
        current_user=current_user,
        summary_cards=summary_cards,
        admin_links=admin_links,
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

    users = User.query.filter_by(isAdmin=False).order_by(User.nome.asc()).all()
    total_ativos = sum(1 for user in users if user.estado == EstadoUser.ativo)
    total_inativos = len(users) - total_ativos

    return render_template(
        "listar_utilizadores.html",
        users=users,
        total_ativos=total_ativos,
        total_inativos=total_inativos,
    )


@main_bp.route("/perfil-utilizador")
def perfil_utilizador():
    if "user_id" not in session:
        flash("Tem de fazer login", "danger")
        return redirect(url_for("auth.login_page"))

    user = User.query.get(session["user_id"])
    return _render_editar_utilizador_form(user, _build_user_form_data(user, {}))


@main_bp.route("/editar-utilizador/<int:user_id>")
def editar_utilizador_page(user_id):
    if "user_id" not in session:
        flash("Tem de fazer login primeiro", "danger")
        return redirect(url_for("auth.login_page"))

    if not session.get("is_admin"):
        flash("Acesso restrito ao administrador", "danger")
        return redirect(url_for("main.index"))

    user = User.query.get_or_404(user_id)
    return _render_editar_utilizador_form(user, _build_user_form_data(user, {}))


@main_bp.route("/editar-utilizador/<int:user_id>", methods=["POST"])
def editar_utilizador(user_id):
    if "user_id" not in session:
        flash("Tem de fazer login primeiro", "danger")
        return redirect(url_for("auth.login_page"))

    user = User.query.get_or_404(user_id)

    if not session.get("is_admin") and session["user_id"] != user_id:
        flash("Acesso restrito", "danger")
        return redirect(url_for("main.index"))

    is_self_edit = session["user_id"] == user.id
    nome = request.form.get("nome", "").strip()
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    data_str = request.form.get("dataNascimento", "").strip()
    estado = request.form.get("estado", "").strip()
    nova_password = request.form.get("password", "")

    form_data = {
        "nome": nome,
        "username": username,
        "email": email,
        "dataNascimento": data_str,
        "estado": estado,
    }

    if not nome or not username or not email or not data_str or not estado:
        flash("Todos os campos obrigatorios devem ser preenchidos.", "danger")
        return _render_editar_utilizador_form(user, form_data)

    if estado not in {"ativo", "inativo"}:
        flash("Estado invalido.", "danger")
        return _render_editar_utilizador_form(user, form_data)

    data_nascimento = _parse_data_nascimento(data_str)
    if data_nascimento is None:
        flash("Data de nascimento invalida.", "danger")
        return _render_editar_utilizador_form(user, form_data)

    if data_nascimento > date.today():
        flash("Data de nascimento invalida.", "danger")
        return _render_editar_utilizador_form(user, form_data)

    if not _email_e_valido(email):
        flash("Email invalido.", "danger")
        return _render_editar_utilizador_form(user, form_data)

    existe_username = User.query.filter(User.username == username, User.id != user.id).first()
    if existe_username:
        flash("Username ja existe.", "danger")
        return _render_editar_utilizador_form(user, form_data)

    existe_email = User.query.filter(User.email == email, User.id != user.id).first()
    if existe_email:
        flash("Email ja existe.", "danger")
        return _render_editar_utilizador_form(user, form_data)

    if not is_self_edit:
        nova_password = ""

    if nova_password:
        password_error = _validar_password(nova_password)
        if password_error:
            flash(password_error, "danger")
            return _render_editar_utilizador_form(user, form_data)

    estado_atual = user.estado
    novo_estado = _normalizar_estado_utilizador(estado)

    user.nome = nome
    user.username = username
    user.email = email
    user.dataNascimento = data_nascimento

    if nova_password:
        user.password = nova_password

    if estado_atual != EstadoUser.inativo and novo_estado == EstadoUser.inativo:
        pode_inativar, mensagem = _pode_inativar_conta(user)

        if not pode_inativar:
            db.session.rollback()
            flash(mensagem, "danger")
            return _render_editar_utilizador_form(user, form_data)

    user.estado = novo_estado
    db.session.commit()

    if is_self_edit:
        session["username"] = user.username

    if is_self_edit and user.estado == EstadoUser.inativo:
        session.clear()
        flash("Conta inativada com sucesso.", "success")
        return redirect(url_for("main.index"))

    flash("Utilizador atualizado com sucesso!", "success")

    if session.get("is_admin"):
        return redirect(url_for("main.editar_utilizador_page", user_id=user.id))

    return redirect(url_for("main.perfil_utilizador"))


@main_bp.route("/alterar-estado-utilizador/<int:user_id>", methods=["POST"])
def alterar_estado_utilizador(user_id):
    if "user_id" not in session:
        flash("Tem de fazer login primeiro", "danger")
        return redirect(url_for("auth.login_page"))

    if not session.get("is_admin"):
        flash("Acesso restrito ao administrador", "danger")
        return redirect(url_for("main.index"))

    user = User.query.get_or_404(user_id)
    novo_estado = request.form.get("estado", "").strip()

    if novo_estado not in {"ativo", "inativo"}:
        flash("Estado invalido.", "danger")
        return redirect(url_for("main.listar_utilizadores"))

    estado_enum = _normalizar_estado_utilizador(novo_estado)
    if user.estado == estado_enum:
        return redirect(url_for("main.listar_utilizadores"))

    if estado_enum == EstadoUser.inativo:
        pode_inativar, mensagem = _pode_inativar_conta(user)
        if not pode_inativar:
            db.session.rollback()
            flash(mensagem, "danger")
            return redirect(url_for("main.listar_utilizadores"))

    user.estado = estado_enum
    db.session.commit()

    flash(
        "Conta ativada com sucesso." if user.estado == EstadoUser.ativo else "Conta inativada com sucesso.",
        "success",
    )
    return redirect(url_for("main.listar_utilizadores"))


@main_bp.route("/reservar-page")
def reservar_page():
    if "user_id" not in session:
        flash("Tem de fazer login primeiro", "danger")
        return redirect(url_for("auth.login_page"))

    return render_template("reservar.html")
