from flask import Blueprint
#from .service import create_user

rotas_utilizador = Blueprint("utilizador", __name__, url_prefix="/utilizador")

@rotas_utilizador.route("login", methods=["POST"])
def login():
	pass

@rotas_utilizador.route("registo", methods=["POST"])
def registo():
	pass

