from flask import Blueprint, render_template
#from .service import create_user

rotas_reserva = Blueprint("reserva", __name__, url_prefix="/reserva")

@rotas_reserva.route("reservar", methods=["POST"])
def reservar_espaco(idEspaco,hora,idUser):
	pass

@rotas_reserva.route("ver_reserva", methods=["GET"])
def ver_reserva():
	return render_template('ver_reserva.html')

@rotas_reserva.route("ver_reservas", methods=["GET"])
def ver_reservas():
	pass

@rotas_reserva.route("cancelar_reserva", methods=["DELETE"])
def cancelar_reserva():
	pass
