from flask import Blueprint, redirect, render_template, url_for, flash, request
from app.models import Espaco, User
from app.extensions import db

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/registar-page")
def registar_page():
    return render_template("registar.html")

@main_bp.route("/espaco-page")
def espaco_page():
    return render_template("espaco.html")

@main_bp.route("/listar-espacos")
def listar_espacos_page():
    espacos = Espaco.query.all()
    return render_template("listar_espacos.html", espacos=espacos)

@main_bp.route("/listar-utilizadores")
def listar_utilizadores():

    users = User.query.all()

    return render_template("listar_utilizadores.html", users=users)


@main_bp.route("/remover-utilizador/<int:user_id>", methods=["POST"])
def remover_utilizador(user_id):

    user = User.query.get_or_404(user_id)

    db.session.delete(user)
    db.session.commit()

    flash("Utilizador removido com sucesso!")

    return redirect(url_for("main.listar_utilizadores"))



@main_bp.route("/editar-utilizador/<int:user_id>")
def editar_utilizador_page(user_id):

    user = User.query.get_or_404(user_id)

    return render_template("editar_utilizador.html", user=user)


@main_bp.route("/editar-utilizador/<int:user_id>", methods=["POST"])
def editar_utilizador(user_id):

    user = User.query.get_or_404(user_id)

    nome = request.form["nome"]
    username = request.form["username"]
    email = request.form["email"]

    if not nome or not username or not email:
        flash("Todos os campos são obrigatórios")
        return redirect(url_for("main.editar_utilizador_page", user_id=user.id))

    existe_username = User.query.filter(
        User.username == username,
        User.id != user.id
    ).first()

    if existe_username:
        flash("Username já existe")
        return redirect(url_for("main.editar_utilizador_page", user_id=user.id))

    existe_email = User.query.filter(
        User.email == email,
        User.id != user.id
    ).first()

    if existe_email:
        flash("Email já existe")
        return redirect(url_for("main.editar_utilizador_page", user_id=user.id))

    user.nome = nome
    user.username = username
    user.email = email

    db.session.commit()

    flash("Utilizador atualizado com sucesso!")
    return redirect(url_for("main.listar_utilizadores"))


@main_bp.route("/reservar-page")
def reservar_page():
    return render_template("reservar.html")