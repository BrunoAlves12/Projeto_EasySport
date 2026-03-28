from flask import Blueprint, render_template, redirect, url_for, flash
from app.models import Pagamento, User, Reserva, db
from datetime import datetime


pagamentos_bp = Blueprint("pagamentos", __name__)

@pagamentos_bp.route("/pagamentos")
def listar_pagamentos():

    pagamentos = Pagamento.query.all()

    users = {u.id: u for u in User.query.all()}
    reservas = {r.id: r for r in Reserva.query.all()}

    return render_template(
        "listar_pagamentos.html",
        pagamentos=pagamentos,
        users=users,
        reservas=reservas
    )

@pagamentos_bp.route("/pagar/<int:pagamento_id>", methods=["POST"])
def pagar(pagamento_id):

    pagamento = Pagamento.query.get_or_404(pagamento_id)

    pagamento.estado = "pago"
    pagamento.dataPagamento = datetime.now()

    db.session.commit()

    flash("Pagamento realizado com sucesso", "success")
    return redirect(url_for("pagamentos.listar_pagamentos"))
