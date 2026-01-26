from flask import Blueprint, request, jsonify
#from .service import create_user

rotas_espaco = Blueprint("espaco", __name__, url_prefix="/espaco")

@rotas_espaco.route("ver_espacos", methods=["GET"])
def ver_espacos():
	pass

@rotas_espaco.route("ver_espaco", methods=["GET"])
def ver_espaco():
	pass

@rotas_espaco.route("cria_espaco", methods=["POST"])
def cria_espaco():
	pass

@rotas_espaco.route("editar_espaco", methods=["PUT"])
def editar_espaco():
	pass

@rotas_espaco.route("remover_espaco", methods=["DELETE"])
def remover_espaco():
	pass