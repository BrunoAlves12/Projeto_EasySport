import calendar
from datetime import date, datetime, time, timedelta

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from app.extensions import db
from app.models import EstadoReserva, Espaco, Pagamento, Reserva, User

reservas_bp = Blueprint("reservas", __name__)

HORA_ABERTURA = 8
HORA_FECHO = 24
PASSO_HORAS = 1
DURACAO_MINIMA_HORAS = 1
MESES_PT = [
    "",
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
]


def _obter_espacos_ativos():
    return Espaco.query.filter_by(ativo=True).order_by(Espaco.nome.asc()).all()


def _obter_espaco_por_id(espaco_id):
    if not espaco_id:
        return None

    return Espaco.query.filter_by(id=espaco_id, ativo=True).first()


def _query_reservas_ativas(espaco_id):
    return Reserva.query.filter(
        Reserva.idEspaco == espaco_id,
        Reserva.estado != EstadoReserva.cancelada,
    )


def _parse_data_reserva(data_str):
    if not data_str:
        return None

    try:
        return datetime.strptime(data_str, "%Y-%m-%d").date()
    except ValueError:
        return None


def _parse_datetime_local(value):
    if not value:
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M")
    except ValueError:
        return None


def _inicio_funcionamento(data_reserva):
    return datetime.combine(data_reserva, time(hour=HORA_ABERTURA))


def _fim_funcionamento(data_reserva):
    if HORA_FECHO == 24:
        return datetime.combine(data_reserva + timedelta(days=1), time.min)

    return datetime.combine(data_reserva, time(hour=HORA_FECHO))


def _formatar_hora(hour_value):
    if hour_value == 24:
        return "00:00"

    return f"{hour_value:02d}:00"


def _reservas_do_periodo(espaco_id, inicio_periodo, fim_periodo):
    return _query_reservas_ativas(espaco_id).filter(
        Reserva.dataInicio < fim_periodo,
        Reserva.dataFim > inicio_periodo,
    ).all()


def _intervalo_conflita(reservas, inicio, fim):
    return any(reserva.dataInicio < fim and reserva.dataFim > inicio for reserva in reservas)


def _duracoes_validas_para_inicio(inicio_slot, fim_funcionamento, reservas):
    duracoes = []
    duracao = DURACAO_MINIMA_HORAS

    while True:
        fim_slot = inicio_slot + timedelta(hours=duracao)

        if fim_slot > fim_funcionamento:
            break

        if _intervalo_conflita(reservas, inicio_slot, fim_slot):
            break

        duracoes.append(
            {
                "horas": duracao,
                "label": f"{duracao} hora" if duracao == 1 else f"{duracao} horas",
                "fim": fim_slot.strftime("%Y-%m-%dT%H:%M"),
                "hora_fim": fim_slot.strftime("%H:%M"),
            }
        )

        duracao += 1

    return duracoes


def _obter_opcoes_do_dia(espaco, data_reserva):
    agora = datetime.now()
    inicio_funcionamento = _inicio_funcionamento(data_reserva)
    fim_funcionamento = _fim_funcionamento(data_reserva)
    reservas = _reservas_do_periodo(espaco.id, inicio_funcionamento, fim_funcionamento)

    inicios = []
    total_slots_unitarios = 0
    slots_unitarios_livres = 0
    hora_cursor = inicio_funcionamento

    while hora_cursor + timedelta(hours=DURACAO_MINIMA_HORAS) <= fim_funcionamento:
        total_slots_unitarios += 1

        if hora_cursor >= agora:
            duracoes = _duracoes_validas_para_inicio(hora_cursor, fim_funcionamento, reservas)
        else:
            duracoes = []

        if duracoes:
            slots_unitarios_livres += 1
            inicios.append(
                {
                    "inicio": hora_cursor.strftime("%Y-%m-%dT%H:%M"),
                    "hora_inicio": hora_cursor.strftime("%H:%M"),
                    "label": hora_cursor.strftime("%H:%M"),
                    "duracoes": duracoes,
                }
            )

        hora_cursor += timedelta(hours=PASSO_HORAS)

    if total_slots_unitarios == 0 or slots_unitarios_livres == 0:
        estado = "indisponivel"
    elif slots_unitarios_livres == total_slots_unitarios:
        estado = "livre"
    else:
        estado = "parcial"

    return {
        "estado": estado,
        "inicios": inicios,
        "horario_funcionamento": {
            "abertura": _formatar_hora(HORA_ABERTURA),
            "fecho": _formatar_hora(HORA_FECHO),
        },
    }


def _serializar_espaco(espaco):
    return {
        "id": espaco.id,
        "nome": espaco.nome,
        "modalidade": (espaco.modalidade or "Espaço desportivo").strip(),
        "preco_hora": round(espaco.precoHora, 2),
        "horario_funcionamento": {
            "abertura": _formatar_hora(HORA_ABERTURA),
            "fecho": _formatar_hora(HORA_FECHO),
        },
    }


def _reserva_respeita_funcionamento(inicio, fim):
    data_reserva = inicio.date()
    return inicio >= _inicio_funcionamento(data_reserva) and fim <= _fim_funcionamento(data_reserva)


@reservas_bp.route("/reservar")
def reservar_page():
    if "user_id" not in session:
        return redirect(url_for("auth.login_page"))

    espacos = _obter_espacos_ativos()
    espaco_id_selecionado = request.args.get("espaco_id", type=int)
    selected_espaco = _obter_espaco_por_id(espaco_id_selecionado)
    hoje = date.today()

    return render_template(
        "reservar.html",
        espacos=espacos,
        selected_espaco=selected_espaco,
        data_minima=hoje.isoformat(),
        calendario_inicial={
            "ano": hoje.year,
            "mes": hoje.month,
        },
        configuracao_reserva={
            "abertura": _formatar_hora(HORA_ABERTURA),
            "fecho": _formatar_hora(HORA_FECHO),
        },
    )


@reservas_bp.route("/api/espacos/<int:espaco_id>/calendario-mensal")
def calendario_mensal(espaco_id):
    if "user_id" not in session:
        return jsonify({"erro": "Sessão inválida"}), 401

    espaco = _obter_espaco_por_id(espaco_id)
    if not espaco:
        return jsonify({"erro": "Espaço não encontrado"}), 404

    ano = request.args.get("ano", type=int)
    mes = request.args.get("mes", type=int)

    if not ano or not mes or mes < 1 or mes > 12:
        return jsonify({"erro": "Mês inválido"}), 400

    hoje = date.today()
    primeiro_dia = date(ano, mes, 1)

    if primeiro_dia < date(hoje.year, hoje.month, 1):
        return jsonify({"erro": "Não é possível consultar meses no passado"}), 400

    _, total_dias = calendar.monthrange(ano, mes)
    dias = []

    for numero_dia in range(1, total_dias + 1):
        data_reserva = date(ano, mes, numero_dia)
        opcoes = _obter_opcoes_do_dia(espaco, data_reserva)

        dias.append(
            {
                "data": data_reserva.isoformat(),
                "dia": numero_dia,
                "estado": opcoes["estado"],
            }
        )

    return jsonify(
        {
            "espaco": _serializar_espaco(espaco),
            "ano": ano,
            "mes": mes,
            "nome_mes": MESES_PT[mes],
            "primeiro_dia_semana": (primeiro_dia.weekday() + 1) % 7,
            "dias": dias,
        }
    )


@reservas_bp.route("/api/espacos/<int:espaco_id>/disponibilidade-dia")
def disponibilidade_dia(espaco_id):
    if "user_id" not in session:
        return jsonify({"erro": "Sessão inválida"}), 401

    espaco = _obter_espaco_por_id(espaco_id)
    if not espaco:
        return jsonify({"erro": "Espaço não encontrado"}), 404

    data_reserva = _parse_data_reserva(request.args.get("data", "").strip())
    if data_reserva is None:
        return jsonify({"erro": "Data inválida"}), 400

    if data_reserva < date.today():
        return jsonify({"erro": "Não é possível reservar datas no passado"}), 400

    opcoes = _obter_opcoes_do_dia(espaco, data_reserva)

    return jsonify(
        {
            "espaco": _serializar_espaco(espaco),
            "data": data_reserva.isoformat(),
            "estado": opcoes["estado"],
            "horario_funcionamento": opcoes["horario_funcionamento"],
            "inicios": opcoes["inicios"],
        }
    )


@reservas_bp.route("/reservar", methods=["POST"])
def criar_reserva():
    if "user_id" not in session:
        return redirect(url_for("auth.login_page"))

    user_id = session["user_id"]
    espaco_id = request.form.get("espaco_id", type=int)
    inicio = _parse_datetime_local(request.form.get("inicio", "").strip())
    fim = _parse_datetime_local(request.form.get("fim", "").strip())

    espaco = _obter_espaco_por_id(espaco_id)
    if not espaco:
        flash("Espaço inválido")
        return redirect(url_for("reservas.reservar_page"))

    if not inicio or not fim:
        flash("Escolhe o dia, a hora de início e a duração da reserva")
        return redirect(url_for("reservas.reservar_page", espaco_id=espaco_id))

    if fim <= inicio:
        flash("Hora do fim inválida")
        return redirect(url_for("reservas.reservar_page", espaco_id=espaco_id))

    if inicio < datetime.now():
        flash("Não é possível reservar datas no passado")
        return redirect(url_for("reservas.reservar_page", espaco_id=espaco_id))

    duracao_horas = (fim - inicio).total_seconds() / 3600
    if duracao_horas < DURACAO_MINIMA_HORAS or int(duracao_horas) != duracao_horas:
        flash("Escolhe uma duração válida para esta reserva")
        return redirect(url_for("reservas.reservar_page", espaco_id=espaco_id))

    if not _reserva_respeita_funcionamento(inicio, fim):
        flash("A reserva tem de respeitar o horário de funcionamento do espaço")
        return redirect(url_for("reservas.reservar_page", espaco_id=espaco_id))

    reservas = _reservas_do_periodo(espaco_id, _inicio_funcionamento(inicio.date()), _fim_funcionamento(inicio.date()))
    if _intervalo_conflita(reservas, inicio, fim):
        flash("Já existe uma reserva para este espaço nesse intervalo")
        return redirect(url_for("reservas.reservar_page", espaco_id=espaco_id))

    reserva = Reserva(
        idUser=user_id,
        idEspaco=espaco_id,
        dataInicio=inicio,
        dataFim=fim,
        estado=EstadoReserva.pendente,
    )

    db.session.add(reserva)
    db.session.commit()

    valor = duracao_horas * espaco.precoHora
    pagamento = Pagamento(
        idUser=user_id,
        idReserva=reserva.id,
        valor=valor,
        estado="pendente",
    )

    db.session.add(pagamento)
    db.session.commit()

    flash("Reserva criada com sucesso")
    return redirect(url_for("reservas.listar_reservas"))


@reservas_bp.route("/reservas")
def listar_reservas():
    reservas = Reserva.query.all()
    users = {u.id: u for u in User.query.all()}
    espacos = {e.id: e for e in Espaco.query.all()}

    return render_template(
        "listar_reservas.html",
        reservas=reservas,
        users=users,
        espacos=espacos,
    )


@reservas_bp.route("/cancelar-reserva/<int:reserva_id>", methods=["POST"])
def cancelar_reserva(reserva_id):
    reserva = Reserva.query.get_or_404(reserva_id)
    reserva.estado = EstadoReserva.cancelada

    db.session.commit()

    flash("Reserva cancelada")
    return redirect(url_for("reservas.listar_reservas"))


@reservas_bp.route("/pagar-reserva/<int:reserva_id>", methods=["POST"])
def pagar_reserva(reserva_id):
    reserva = Reserva.query.get_or_404(reserva_id)
    reserva.estado = EstadoReserva.confirmada

    db.session.commit()

    flash("Pagamento confirmado e reserva concluída")
    return redirect(url_for("reservas.listar_reservas"))


@reservas_bp.route("/minhas-reservas")
def minha_reservas():
    if "user_id" not in session:
        return redirect(url_for("auth.login_page"))

    reservas = Reserva.query.filter_by(idUser=session["user_id"]).all()
    users = {u.id: u for u in User.query.filter_by(isAdmin=False).all()}
    espacos = {e.id: e for e in Espaco.query.all()}

    return render_template(
        "listar_reservas.html",
        reservas=reservas,
        users=users,
        espacos=espacos,
    )
