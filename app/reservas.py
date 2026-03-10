from flask import Blueprint, request, flash, redirect, url_for, render_template
from app.models import Pagamento, Reserva, User, Espaco, Pagamento
from app.extensions import db
from datetime import datetime

reservas_bp = Blueprint("reservas", __name__)

@reservas_bp.route("/reservar")
def reservar_page():
    users = User.query.all()
    espacos = Espaco.query.filter_by(ativo=True).all()
    return render_template("reservar.html", users=users, espacos=espacos)

@reservas_bp.route("/reservar", methods=["POST"])
def criar_reserva():

    user_id = request.form["user_id"]
    espaco_id = request.form["espaco_id"]

    inicio_str = request.form["inicio"]
    fim_str = request.form["fim"]

    #validações
    if not inicio_str or not fim_str:
        flash("Preencha as datas da reserva")
        return redirect(url_for("reservas.reservar_page"))

    inicio = datetime.strptime(request.form["inicio"], "%Y-%m-%dT%H:%M")
    fim = datetime.strptime(request.form["fim"], "%Y-%m-%dT%H:%M")

    #validações
    if fim <= inicio:
        flash("Hora do fim inválida")
        return redirect(url_for("reservas.reservar_page"))
    
    reserva_existente = Reserva.query.filter(
        Reserva.idEspaco == espaco_id,
        Reserva.dataInicio < fim,
        Reserva.dataFim > inicio,
    ).first()

    if reserva_existente:
        flash ("Já existe uma reserva para este espaço nesse horário")
        return redirect(url_for("reservas.reservar_page"))

    reserva = Reserva(
        idUser = user_id,
        idEspaco = espaco_id,
        dataInicio = inicio,
        dataFim = fim,
        estado = "pendente"
    )

    db.session.add(reserva)
    db.session.commit()

    # pagamento
    espaco = Espaco.query.get(espaco_id)
    horas = (fim - inicio).total_seconds() / 3600
    valor = horas * espaco.precoHora

    pagamento = Pagamento(
    idUser=user_id,
    idReserva=reserva.id,
    valor=valor,
    estado="pendente"
    )

    db.session.add(pagamento)
    db.session.commit()

    flash("Reserva criada com sucesso")
    return redirect(url_for("reservas.listar_reservas"))

@reservas_bp.route("/reservas")
def listar_reservas():

    reservas = Reserva.query.all()

    reservas = Reserva.query.all()
    users = {u.id: u for u in User.query.all()}
    espacos = {e.id: e for e in Espaco.query.all()}

    return render_template(
        "listar_reservas.html",
        reservas=reservas,
        users=users,
        espacos=espacos
    )

@reservas_bp.route("/cancelar-reserva/<int:reserva_id>", methods=["POST"])
def cancelar_reserva(reserva_id):

    reserva = Reserva.query.get_or_404(reserva_id)

    reserva.estado = "cancelada"

    db.session.commit()

    flash("Reserva cancelada")
    return redirect(url_for("reservas.listar_reservas"))   


@reservas_bp.route("/pagar-reserva/<int:reserva_id>", methods=["POST"])
def pagar_reserva(reserva_id):

    reserva = Reserva.query.get_or_404(reserva_id)

    reserva.estado = "confirmada"

    db.session.commit()

    flash("Pagamento confirmado e reserva concluída")

    return redirect(url_for("reservas.listar_reservas"))