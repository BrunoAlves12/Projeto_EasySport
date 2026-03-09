from flask import Blueprint, redirect, render_template, url_for, flash
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
