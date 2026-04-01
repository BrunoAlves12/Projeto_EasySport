import os
import re
from datetime import datetime

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from app.extensions import db
from app.models import EstadoReserva, Espaco, Pagamento, Reserva, User

pagamentos_bp = Blueprint("pagamentos", __name__)


def _utilizador_autorizado_para_reserva(reserva):
    return session.get("is_admin") or reserva.idUser == session.get("user_id")


def _ultimos_quatro_digitos(numero_cartao):
    digitos = "".join(char for char in numero_cartao if char.isdigit())
    return digitos[-4:] if len(digitos) >= 4 else ""


def _validar_dados_pagamento(form_data):
    numero_cartao = "".join(char for char in form_data["numeroCartao"] if char.isdigit())
    cvv = "".join(char for char in form_data["cvv"] if char.isdigit())
    validade = form_data["validade"]

    if not numero_cartao.isdigit() or not 12 <= len(numero_cartao) <= 19:
        return "Introduz um numero de cartao valido com 12 a 19 digitos."

    validade_match = re.fullmatch(r"(\d{2})/(\d{2})", validade)
    if not validade_match:
        return "Introduz a validade no formato MM/AA."

    mes = int(validade_match.group(1))
    if mes < 1 or mes > 12:
        return "Introduz um mes de validade entre 01 e 12."

    if not re.fullmatch(r"\d{3,4}", cvv):
        return "Introduz um CVV com 3 ou 4 digitos."

    form_data["numeroCartao"] = numero_cartao
    form_data["cvv"] = cvv
    form_data["validade"] = validade
    return None


def _build_checkout_context(reserva, pagamento):
    espaco = Espaco.query.get(reserva.idEspaco)
    utilizador = User.query.get(reserva.idUser)
    duracao_horas = int((reserva.dataFim - reserva.dataInicio).total_seconds() / 3600)
    imagem_espaco = current_app.config["ESPACO_IMAGEM_DEFAULT"]

    if espaco and espaco.imagem:
        caminho_imagem = os.path.join(current_app.static_folder, espaco.imagem.replace("/", os.sep))
        if os.path.exists(caminho_imagem):
            imagem_espaco = espaco.imagem

    return {
        "reserva": reserva,
        "espaco": espaco,
        "pagamento": pagamento,
        "imagem_espaco": imagem_espaco,
        "resumo": {
            "espaco": espaco.nome if espaco else "Espaco indisponivel",
            "modalidade": (espaco.modalidade or "Espaco desportivo").strip() if espaco else "Espaco desportivo",
            "data": reserva.dataInicio.strftime("%d/%m/%Y"),
            "inicio": reserva.dataInicio.strftime("%H:%M"),
            "fim": reserva.dataFim.strftime("%H:%M"),
            "duracao": f"{duracao_horas} hora" if duracao_horas == 1 else f"{duracao_horas} horas",
            "preco_hora": f"{(espaco.precoHora if espaco else 0):.2f} EUR",
            "total": f"{pagamento.valor:.2f} EUR",
        },
        "form_data": {
            "nomeFaturacao": pagamento.nomeFaturacao or (utilizador.nome if utilizador else ""),
            "emailFaturacao": pagamento.emailFaturacao or (utilizador.email if utilizador else ""),
            "morada": pagamento.morada or "",
            "codigoPostal": pagamento.codigoPostal or "",
            "localidade": pagamento.localidade or "",
            "pais": pagamento.pais or "Portugal",
            "numeroCartao": "",
            "validade": "",
            "cvv": "",
        },
    }


@pagamentos_bp.route("/checkout/<int:reserva_id>")
def checkout_reserva(reserva_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login_page"))

    reserva = Reserva.query.get_or_404(reserva_id)
    if not _utilizador_autorizado_para_reserva(reserva):
        flash("Acesso restrito", "danger")
        return redirect(url_for("main.index"))

    pagamento = Pagamento.query.filter_by(idReserva=reserva.id).first_or_404()

    if reserva.estado == EstadoReserva.cancelada or pagamento.estado == "cancelado":
        flash("Nao e possivel pagar uma reserva cancelada", "danger")
        return redirect(url_for("reservas.minha_reservas"))

    if pagamento.estado == "pago":
        flash("Esta reserva ja se encontra paga", "success")
        return redirect(url_for("reservas.minha_reservas"))

    return render_template("checkout_pagamento.html", **_build_checkout_context(reserva, pagamento))


@pagamentos_bp.route("/checkout/<int:reserva_id>", methods=["POST"])
def processar_checkout_reserva(reserva_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login_page"))

    reserva = Reserva.query.get_or_404(reserva_id)
    if not _utilizador_autorizado_para_reserva(reserva):
        flash("Acesso restrito", "danger")
        return redirect(url_for("main.index"))

    pagamento = Pagamento.query.filter_by(idReserva=reserva.id).first_or_404()

    if reserva.estado == EstadoReserva.cancelada or pagamento.estado == "cancelado":
        flash("Nao e possivel pagar uma reserva cancelada", "danger")
        return redirect(url_for("reservas.minha_reservas"))

    if pagamento.estado == "pago":
        flash("Esta reserva ja se encontra paga", "success")
        return redirect(url_for("reservas.minha_reservas"))

    form_data = {
        "nomeFaturacao": request.form.get("nomeFaturacao", "").strip(),
        "emailFaturacao": request.form.get("emailFaturacao", "").strip(),
        "morada": request.form.get("morada", "").strip(),
        "codigoPostal": request.form.get("codigoPostal", "").strip(),
        "localidade": request.form.get("localidade", "").strip(),
        "pais": request.form.get("pais", "").strip(),
        "numeroCartao": request.form.get("numeroCartao", "").strip(),
        "validade": request.form.get("validade", "").strip(),
        "cvv": request.form.get("cvv", "").strip(),
    }

    if not all(form_data.values()):
        flash("Preenche todos os dados de faturacao e pagamento", "danger")
        context = _build_checkout_context(reserva, pagamento)
        context["form_data"] = form_data
        return render_template("checkout_pagamento.html", **context)

    mensagem_validacao = _validar_dados_pagamento(form_data)
    if mensagem_validacao:
        flash(mensagem_validacao, "danger")
        context = _build_checkout_context(reserva, pagamento)
        context["form_data"] = form_data
        return render_template("checkout_pagamento.html", **context)

    ultimos4 = _ultimos_quatro_digitos(form_data["numeroCartao"])

    pagamento.nomeFaturacao = form_data["nomeFaturacao"]
    pagamento.emailFaturacao = form_data["emailFaturacao"]
    pagamento.morada = form_data["morada"]
    pagamento.codigoPostal = form_data["codigoPostal"]
    pagamento.localidade = form_data["localidade"]
    pagamento.pais = form_data["pais"]
    pagamento.ultimos4Cartao = ultimos4
    pagamento.estado = "pago"
    pagamento.dataPagamento = datetime.now()

    reserva.estado = EstadoReserva.confirmada

    db.session.commit()

    flash("Pagamento realizado com sucesso. A reserva ficou confirmada.", "success")
    return redirect(url_for("reservas.minha_reservas"))
