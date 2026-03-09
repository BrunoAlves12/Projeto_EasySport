from flask import Blueprint, request
from app.models import Reserva
from app.extensions import db
from datetime import datetime

reservas_bp = Blueprint("reservas", __name__)

@reservas_bp.route("/reservas", methods=["POST"])
def criar_reserva():

    user_id = request.json["user_id"]
    espaco_id = request.json["espaco_id"]

    inicio = datetime.fromisoformat(request.json["inicio"])
    fim = datetime.fromisoformat(request.json["fim"])

    #validações
    if fim <= inicio:
        return {"erro": "Hora do fim inválida"}
    
    reserva_existente = Reserva.query.filter(
        Reserva.idEspaco == espaco_id,
        Reserva.dataInicio < fim,
        Reserva.dataFim > inicio,
    ).first()

    if reserva_existente:
        return {"erro": "Já existe uma reserva para este espaço nesse horário"}

    reserva = Reserva(
        idUser = user_id,
        idEspaco = espaco_id,
        dataInicio = inicio,
        dataFim = fim,
        estado = "ativa"
    )

    db.session.add(reserva)
    db.session.commit()

    return {"mensagem": "Reserva criada com sucesso"}

@reservas_bp.route("/reservas", methods=["GET"])
def listar_reservas():

    reservas = Reserva.query.all()

    resultado = []  
    for r in reservas:
        resultado.append({
            "id": r.id,
            "user": r.idUser,
            "espaco": r.idEspaco,
            "inicio": r.dataInicio,
            "fim": r.dataFim,
            "estado": r.estado
        })
    return resultado
