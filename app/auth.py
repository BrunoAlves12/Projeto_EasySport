from flask import Blueprint, render_template, request, redirect, url_for,flash
from app.models import User
from app.extensions import db
import re
from datetime import datetime, date

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET"])
def register_page():
    return render_template("registar.html")

@auth_bp.route("/register", methods=["POST"])
def register():

    nome = request.form["nome"]
    email = request.form["email"]
    password = request.form["password"]
    username = request.form["username"]
    
    #estava a dar erro, não estava a converter a data de string para date
    data_str = request.form["dataNascimento"]
    dataNascimento = datetime.strptime(data_str, "%Y-%m-%d").date()

    #validações
    if not nome or not email or not password or not username or not dataNascimento:
        flash("Todos os campos são obrigatórios!")
        return redirect(url_for("auth.register_page"))
    
    if "@" not in email:
        flash("Email inválido!")
        return redirect(url_for("auth.register_page"))
    
    partes = email.split("@")

    if len(partes) != 2 or "." not in partes[1]:
        flash("Email inválido")
        return redirect(url_for("auth.register_page"))
    
    # o metodo first retorna o primeiro resultado encontrado ou None se não encontrar nenhum
    if User.query.filter_by(email=email).first():
        flash("Email já registado")
        return redirect(url_for("auth.register_page"))
    
    
    if User.query.filter_by(username=username).first():
        flash("Username já existe")
        return redirect(url_for("auth.register_page"))
    
    if dataNascimento > date.today():
        flash("Data de nascimento inválida")
        return redirect(url_for("auth.register_page"))

    user = User(
        nome=nome, 
        email=email, 
        username=username,
        password=password,
        dataNascimento=dataNascimento
    )

    db.session.add(user)
    db.session.commit()

    flash("Utilizador criado com sucesso!")
    return redirect(url_for("main.index"))
