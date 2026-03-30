from datetime import date, datetime

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy import or_

from app.extensions import db
from app.models import EstadoUser, User

auth_bp = Blueprint("auth", __name__)


def _render_register_form(form_data=None):
    return render_template("registar.html", form_data=form_data or {})


def _render_login_form(form_data=None):
    return render_template("login.html", form_data=form_data or {})


@auth_bp.before_app_request
def impedir_sessao_de_conta_inativa():
    endpoint = request.endpoint or ""

    if not session.get("user_id"):
        return None

    if endpoint == "static" or endpoint.startswith("auth."):
        return None

    user = User.query.get(session["user_id"])

    if user is None or user.estado == EstadoUser.inativo:
        session.clear()
        flash("A tua conta esta inativa. Nao e possivel continuar com a sessao.", "danger")
        return redirect(url_for("main.index"))

    session["username"] = user.username
    session["is_admin"] = user.isAdmin
    return None


def _validar_password(password):
    if len(password) < 8 or len(password) > 15:
        return "A password precisa de ter entre 8 e 15 caracteres."

    numero = False
    maiuscula = False
    minuscula = False
    especial = False

    for char in password:
        if char.isdigit():
            numero = True
        elif char.isalpha():
            if char.isupper():
                maiuscula = True
            else:
                minuscula = True
        else:
            especial = True

    if not numero or not maiuscula or not minuscula or not especial:
        return "A password precisa de ter uma maiuscula, uma minuscula, um numero e um caracter especial."

    return None


@auth_bp.route("/register", methods=["GET"])
def register_page():
    return _render_register_form()


@auth_bp.route("/register", methods=["POST"])
def register():
    nome = request.form.get("nome", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    username = request.form.get("username", "").strip()
    data_str = request.form.get("dataNascimento", "").strip()

    form_data = {
        "nome": nome,
        "email": email,
        "username": username,
        "dataNascimento": data_str,
    }

    if not nome or not email or not password or not username or not data_str:
        flash("Todos os campos sao obrigatorios!", "danger")
        return _render_register_form(form_data)

    try:
        data_nascimento = datetime.strptime(data_str, "%Y-%m-%d").date()
    except ValueError:
        flash("Data de nascimento invalida", "danger")
        return _render_register_form(form_data)

    password_error = _validar_password(password)
    if password_error:
        flash(password_error, "danger")
        return _render_register_form(form_data)

    if "@" not in email:
        flash("Email invalido!", "danger")
        return _render_register_form(form_data)

    partes = email.split("@")

    if len(partes) != 2 or "." not in partes[1]:
        flash("Email invalido", "danger")
        return _render_register_form(form_data)

    if User.query.filter_by(email=email).first():
        flash("Email ja registado", "danger")
        return _render_register_form(form_data)

    if User.query.filter_by(username=username).first():
        flash("Username ja existe", "danger")
        return _render_register_form(form_data)

    if data_nascimento > date.today():
        flash("Data de nascimento invalida", "danger")
        return _render_register_form(form_data)

    user = User(
        nome=nome,
        email=email,
        username=username,
        password=password,
        dataNascimento=data_nascimento,
    )

    db.session.add(user)
    db.session.commit()

    flash("Utilizador criado com sucesso!", "success")
    return redirect(url_for("main.espacos_homepage"))


@auth_bp.route("/login")
def login_page():
    return _render_login_form()


@auth_bp.route("/login", methods=["POST"])
def login():
    login_value = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    form_data = {"login": login_value}

    if not login_value or not password:
        flash("Preencha todos os campos", "danger")
        return _render_login_form(form_data)

    user = User.query.filter(
        or_(
            User.username == login_value,
            User.email == login_value,
        )
    ).first()

    if not user or user.password != password:
        flash("Credenciais invalidas", "danger")
        return _render_login_form(form_data)

    if user.estado == EstadoUser.inativo:
        flash("A conta esta inativa. Nao e possivel iniciar sessao.", "danger")
        return _render_login_form(form_data)

    session["user_id"] = user.id
    session["username"] = user.username
    session["is_admin"] = user.isAdmin

    flash("Login efetuado com sucesso", "success")

    if user.isAdmin:
        return redirect(url_for("main.admin_dashboard"))

    return redirect(url_for("main.espacos_homepage"))


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Sessao terminada", "success")
    return redirect(url_for("main.index"))
