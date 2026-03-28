from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import EstadoUser, User
from app.extensions import db
from datetime import datetime, date

auth_bp = Blueprint("auth", __name__)


def _render_register_form(form_data=None):
    return render_template("registar.html", form_data=form_data or {})


def _render_login_form(form_data=None):
    return render_template("login.html", form_data=form_data or {})


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
        flash("Todos os campos são obrigatórios!", "danger")
        return _render_register_form(form_data)

    try:
        data_nascimento = datetime.strptime(data_str, "%Y-%m-%d").date()
    except ValueError:
        flash("Data de nascimento inválida", "danger")
        return _render_register_form(form_data)

    if len(password) < 8 or len(password) > 15:
        flash("A password precisa de ter entre 8 e 15 caracteres.", "danger")
        return _render_register_form(form_data)

    numero_caracteres = False
    maiuscula = False
    minuscula = False
    especial = False

    for char in password:
        if char.isdigit():
            numero_caracteres = True
        elif char.isalpha():
            if char.isupper():
                maiuscula = True
            else:
                minuscula = True
        else:
            especial = True

    if not numero_caracteres or not maiuscula or not minuscula or not especial:
        flash("A password precisa de ter uma maiúscula, uma minúscula, um número e um carácter especial.", "danger")
        return _render_register_form(form_data)

    if "@" not in email:
        flash("Email inválido!", "danger")
        return _render_register_form(form_data)

    partes = email.split("@")

    if len(partes) != 2 or "." not in partes[1]:
        flash("Email inválido", "danger")
        return _render_register_form(form_data)

    if User.query.filter_by(email=email).first():
        flash("Email já registado", "danger")
        return _render_register_form(form_data)

    if User.query.filter_by(username=username).first():
        flash("Username já existe", "danger")
        return _render_register_form(form_data)

    if data_nascimento > date.today():
        flash("Data de nascimento inválida", "danger")
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
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    form_data = {"username": username}

    if not username or not password:
        flash("Preencha todos os campos", "danger")
        return _render_login_form(form_data)

    user = User.query.filter_by(username=username).first()

    if not user or user.password != password:
        flash("Credenciais inválidas", "danger")
        return _render_login_form(form_data)

    if user.estado == EstadoUser.inativo:
        flash("A conta está inativa. Contacte o administrador.", "danger")
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
    flash("Sessão Terminada", "success")
    return redirect(url_for("main.index"))
