import random
from datetime import date, datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy import func

from app.access import admin_required, login_required
from app.auth import _hash_password, _nome_tem_numero, _tem_idade_minima, _validar_password
from app.extensions import db
from app.models import EstadoReserva, EstadoUser, Espaco, Pagamento, Reserva, User
from app.security import imagem_segura

main_bp = Blueprint("main", __name__)


# Escolhe os espacos em destaque para a homepage.
def _destaques_homepage():
    espacos = Espaco.query.filter_by(ativo=True).all()
    quantidade = min(3, len(espacos))

    if quantidade == 0:
        return [], False

    espacos_destaque = random.sample(espacos, quantidade)

    for espaco in espacos_destaque:
        espaco.imagem_homepage = imagem_segura(espaco.imagem)
        espaco.modalidade_homepage = (espaco.modalidade or "Espaco desportivo").strip()
        espaco.descricao_curta = (espaco.descricao or "Espaco pronto para reserva.").strip()

    return espacos_destaque, len(espacos) > quantidade


# Devolve o utilizador autenticado na sessao atual.
def _utilizador_atual():
    if not session.get("user_id"):
        return None

    return User.query.get(session["user_id"])


# Formata valores monetarios para apresentacao.
def _formatar_moeda(valor):
    return f"{(valor or 0):.2f} EUR"


# Mostra a duracao media de forma curta.
def _formatar_duracao_media(horas):
    if not horas:
        return "-"

    if float(horas).is_integer():
        horas = int(horas)
        return f"{horas} hora" if horas == 1 else f"{horas} horas"

    return f"{horas:.1f} horas"


# Converte datas dos filtros de estatisticas.
def _parse_data_filtro(data_str):
    if not data_str:
        return None

    try:
        return datetime.strptime(data_str, "%Y-%m-%d").date()
    except ValueError:
        return None


# Calcula o intervalo usado nos filtros de periodo.
def _intervalo_periodo(periodo, data_inicio=None, data_fim=None):
    agora = datetime.now()

    if periodo == "hoje":
        inicio = datetime(agora.year, agora.month, agora.day)
        return inicio, inicio + timedelta(days=1)

    if periodo == "mes":
        inicio = datetime(agora.year, agora.month, 1)
        if agora.month == 12:
            return inicio, datetime(agora.year + 1, 1, 1)

        return inicio, datetime(agora.year, agora.month + 1, 1)

    if periodo == "mes_passado":
        primeiro_mes_atual = datetime(agora.year, agora.month, 1)
        if agora.month == 1:
            inicio = datetime(agora.year - 1, 12, 1)
        else:
            inicio = datetime(agora.year, agora.month - 1, 1)

        return inicio, primeiro_mes_atual

    if periodo == "ano":
        inicio = datetime(agora.year, 1, 1)
        return inicio, datetime(agora.year + 1, 1, 1)

    if periodo == "ano_passado":
        return datetime(agora.year - 1, 1, 1), datetime(agora.year, 1, 1)

    if periodo == "personalizado" and data_inicio and data_fim:
        inicio = datetime.combine(data_inicio, datetime.min.time())
        fim = datetime.combine(data_fim + timedelta(days=1), datetime.min.time())
        return inicio, fim

    return None, None


# Cria o texto visivel do periodo selecionado.
def _label_periodo(periodo, periodos, data_inicio=None, data_fim=None):
    if periodo == "personalizado" and data_inicio and data_fim:
        return f"{data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"

    return periodos[periodo]


# Aplica o intervalo de datas a queries baseadas em reservas.
def _filtrar_periodo(query, inicio, fim):
    if inicio and fim:
        return query.filter(Reserva.dataInicio >= inicio, Reserva.dataInicio < fim)

    return query


# Monta a query de pagamentos pagos no periodo escolhido.
def _pagamentos_pagos(inicio, fim):
    query = Pagamento.query.join(Reserva, Pagamento.idReserva == Reserva.id).filter(Pagamento.estado == "pago")

    return _filtrar_periodo(query, inicio, fim)


# Calcula as metricas do espaco selecionado.
def _stats_espaco(espaco_id, inicio, fim):
    query = Reserva.query

    if espaco_id:
        query = query.filter(Reserva.idEspaco == espaco_id)

    query = _filtrar_periodo(query, inicio, fim)

    total_reservas = query.count()
    reservas_confirmadas = query.filter(Reserva.estado == EstadoReserva.confirmada).count()
    reservas_canceladas = query.filter(Reserva.estado == EstadoReserva.cancelada).count()

    receita_query = _pagamentos_pagos(inicio, fim)
    if espaco_id:
        receita_query = receita_query.filter(Reserva.idEspaco == espaco_id)

    receita = receita_query.with_entities(func.coalesce(func.sum(Pagamento.valor), 0)).scalar()
    duracao_media = query.with_entities(
        func.avg((func.julianday(Reserva.dataFim) - func.julianday(Reserva.dataInicio)) * 24)
    ).scalar()

    return {
        "total_reservas": total_reservas,
        "reservas_confirmadas": reservas_confirmadas,
        "reservas_canceladas": reservas_canceladas,
        "receita_label": _formatar_moeda(receita),
        "duracao_media_label": _formatar_duracao_media(duracao_media),
    }


# Calcula as metricas globais do sistema.
def _stats_globais(inicio, fim):
    faturacao = _pagamentos_pagos(inicio, fim).with_entities(
        func.coalesce(func.sum(Pagamento.valor), 0)
    ).scalar()

    cliente_top = _filtrar_periodo(
        db.session.query(User.nome, func.count(Reserva.id).label("total"))
        .join(Reserva, Reserva.idUser == User.id)
        .filter(User.isAdmin.is_(False)),
        inicio,
        fim,
    ).group_by(User.id).order_by(func.count(Reserva.id).desc(), User.nome.asc()).first()

    espaco_top = _filtrar_periodo(
        db.session.query(Espaco.nome, func.count(Reserva.id).label("total"))
        .join(Reserva, Reserva.idEspaco == Espaco.id),
        inicio,
        fim,
    ).group_by(Espaco.id).order_by(func.count(Reserva.id).desc(), Espaco.nome.asc()).first()

    return {
        "faturacao_total_label": _formatar_moeda(faturacao),
        "cliente_top": cliente_top.nome if cliente_top else "Sem reservas",
        "cliente_top_total": cliente_top.total if cliente_top else 0,
        "espaco_top": espaco_top.nome if espaco_top else "Sem reservas",
        "espaco_top_total": espaco_top.total if espaco_top else 0,
    }


# Renderiza o formulario de utilizador com contexto de permissao.
def _render_form_utilizador(user, form_data=None):
    is_self_edit = session.get("user_id") == user.id
    is_admin_editing_other = session.get("is_admin") and not is_self_edit

    return render_template(
        "editar_utilizador.html",
        user=user,
        form_data=form_data or {},
        is_self_edit=is_self_edit,
        is_admin_editing_other=is_admin_editing_other,
    )


# Converte a data de nascimento enviada no formulario.
def _parse_data_nascimento(data_str):
    try:
        return datetime.strptime(data_str, "%Y-%m-%d").date()
    except ValueError:
        return None


# Valida o formato simples de email usado nos formularios.
def _email_valido(email):
    if "@" not in email:
        return False

    partes = email.split("@")
    return len(partes) == 2 and "." in partes[1]


# Converte o valor do formulario para o enum do utilizador.
def _normalizar_estado_user(estado):
    return EstadoUser.ativo if estado == "ativo" else EstadoUser.inativo


# Lista reservas futuras que ainda bloqueiam alteracoes da conta.
def _reservas_ativas_user(user_id):
    agora = datetime.now()
    return Reserva.query.filter(
        Reserva.idUser == user_id,
        Reserva.dataFim >= agora,
        Reserva.estado.in_([EstadoReserva.pendente, EstadoReserva.confirmada]),
    ).all()


# Verifica se uma conta pode ser inativada sem reservas confirmadas.
def _pode_inativar_conta(user):
    reservas_ativas = _reservas_ativas_user(user.id)
    reservas_confirmadas = [reserva for reserva in reservas_ativas if reserva.estado == EstadoReserva.confirmada]

    if reservas_confirmadas:
        return False, "Nao e possivel inativar a conta porque existem reservas confirmadas."

    reservas_pendentes = [reserva for reserva in reservas_ativas if reserva.estado == EstadoReserva.pendente]

    for reserva in reservas_pendentes:
        reserva.estado = EstadoReserva.cancelada
        pagamento = Pagamento.query.filter_by(idReserva=reserva.id).first()

        if pagamento and pagamento.estado != "pago":
            pagamento.estado = "cancelado"
            pagamento.dataPagamento = None

    return True, None


# Junta dados atuais e enviados para voltar a mostrar o formulario.
def _dados_form_user(user, form_data):
    return {
        "nome": form_data.get("nome", user.nome),
        "username": form_data.get("username", user.username),
        "email": form_data.get("email", user.email),
        "dataNascimento": form_data.get(
            "dataNascimento",
            user.dataNascimento.isoformat() if user.dataNascimento else "",
        ),
        "estado": form_data.get("estado", user.estado.value),
    }


@main_bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        return redirect(url_for("main.index"))

    if session.get("user_id"):
        if session.get("is_admin"):
            return redirect(url_for("main.admin_dashboard"))

        return redirect(url_for("main.espacos_homepage"))

    return render_template("landing.html")


@main_bp.route("/espacos")
def espacos_homepage():
    if session.get("is_admin"):
        return redirect(url_for("main.admin_dashboard"))

    current_user = _utilizador_atual()
    espacos_destaque, mostrar_botao_mais_espacos = _destaques_homepage()

    return render_template(
        "index.html",
        espacos_destaque=espacos_destaque,
        mostrar_botao_mais_espacos=mostrar_botao_mais_espacos,
        current_user=current_user,
    )


@main_bp.route("/admin")
@admin_required
def admin_dashboard():
    current_user = _utilizador_atual()
    now = datetime.now()
    inicio_hoje = datetime(now.year, now.month, now.day)
    inicio_amanha = inicio_hoje + timedelta(days=1)

    reservas_hoje = Reserva.query.filter(
        Reserva.dataInicio >= inicio_hoje,
        Reserva.dataInicio < inicio_amanha,
    ).count()

    utilizadores_recentes = User.query.filter_by(isAdmin=False).order_by(User.id.desc()).limit(3).all()
    espacos_ativos = Espaco.query.filter_by(ativo=True).count()
    pagamentos_pendentes = Pagamento.query.join(
        Reserva,
        Pagamento.idReserva == Reserva.id,
    ).filter(
        Pagamento.estado == "pendente",
        Reserva.estado == EstadoReserva.pendente,
    ).count()

    recent_names = ", ".join(user.nome for user in reversed(utilizadores_recentes))
    if not recent_names:
        recent_names = "Sem novos registos recentes"

    summary_cards = [
        {
            "titulo": "Reservas para hoje",
            "valor": reservas_hoje,
            "detalhe": "Reservas com inicio marcado para hoje.",
            "icone": "calendar",
        },
        {
            "titulo": "Utilizadores recentes",
            "valor": len(utilizadores_recentes),
            "detalhe": recent_names,
            "icone": "users",
        },
        {
            "titulo": "Espacos ativos",
            "valor": espacos_ativos,
            "detalhe": "Espacos atualmente disponiveis na plataforma.",
            "icone": "spaces",
        },
        {
            "titulo": "Pagamentos pendentes",
            "valor": pagamentos_pendentes,
            "detalhe": "Pagamentos ainda por regularizar.",
            "icone": "payments",
        },
    ]

    admin_links = [
        {
            "titulo": "Gerir utilizadores",
            "texto": "Consulta, edita e organiza os utilizadores registados na plataforma.",
            "rota": url_for("main.listar_utilizadores"),
            "botao": "Abrir utilizadores",
            "icone": "users",
        },
        {
            "titulo": "Gerir espacos",
            "texto": "Adiciona novos espacos e controla a disponibilidade dos espacos existentes.",
            "rota": url_for("main.listar_espacos_page"),
            "botao": "Abrir espacos",
            "icone": "spaces",
        },
        {
            "titulo": "Consultar reservas",
            "texto": "Acompanha todas as reservas e confirma rapidamente o estado de cada pedido.",
            "rota": url_for("reservas.listar_reservas"),
            "botao": "Ver reservas",
            "icone": "calendar",
        },
        {
            "titulo": "Estatísticas do Sistema",
            "texto": "Visualiza dados da plataforma como reservas, faturação e utilização dos espaços.",
            "rota": url_for("main.estatisticas_sistema"),
            "botao": "Abrir estatísticas",
            "icone": "analytics",
        },
    ]

    return render_template(
        "admin.html",
        current_user=current_user,
        summary_cards=summary_cards,
        admin_links=admin_links,
    )


@main_bp.route("/admin/estatisticas")
@admin_required
def estatisticas_sistema():
    periodos = {
        "hoje": "Hoje",
        "mes": "Este mês",
        "mes_passado": "Mês passado",
        "ano": "Este ano",
        "ano_passado": "Ano passado",
        "todos": "Todos",
        "personalizado": "Personalizado",
    }
    periodo = request.args.get("periodo", "mes").strip()
    if periodo not in periodos:
        periodo = "mes"

    data_inicio = _parse_data_filtro(request.args.get("data_inicio", "").strip())
    data_fim = _parse_data_filtro(request.args.get("data_fim", "").strip())

    if periodo == "personalizado":
        if not data_inicio or not data_fim:
            flash("Escolhe a data inicial e a data final para o periodo personalizado.", "danger")
        elif data_inicio > data_fim:
            flash("A data inicial deve ser anterior ou igual a data final.", "danger")
            data_inicio = None
            data_fim = None

    espacos = Espaco.query.order_by(Espaco.nome.asc()).all()
    espaco_id = request.args.get("espaco", type=int)
    espaco_selecionado = None

    if espaco_id:
        espaco_selecionado = Espaco.query.get(espaco_id)
        if not espaco_selecionado:
            espaco_id = None

    inicio_periodo, fim_periodo = _intervalo_periodo(periodo, data_inicio, data_fim)
    estatisticas_espaco = _stats_espaco(espaco_id, inicio_periodo, fim_periodo)
    resumo_global = _stats_globais(inicio_periodo, fim_periodo)
    periodo_label = _label_periodo(periodo, periodos, data_inicio, data_fim)

    contexto_espaco = {
        "nome": espaco_selecionado.nome if espaco_selecionado else "Todos os espaços",
        "modalidade": (espaco_selecionado.modalidade or "Espaço desportivo").strip() if espaco_selecionado else "Visão agregada",
        "imagem": imagem_segura(espaco_selecionado.imagem if espaco_selecionado else None),
    }

    return render_template(
        "estatisticas.html",
        espacos=espacos,
        filtros={
            "espaco": espaco_id or "",
            "periodo": periodo,
            "data_inicio": data_inicio.isoformat() if data_inicio else "",
            "data_fim": data_fim.isoformat() if data_fim else "",
        },
        periodos=periodos,
        periodo_label=periodo_label,
        contexto_espaco=contexto_espaco,
        estatisticas_espaco=estatisticas_espaco,
        resumo_global=resumo_global,
    )


@main_bp.route("/registar-page")
def registar_page():
    return render_template("registar.html", form_data={})


@main_bp.route("/espaco-page")
@admin_required
def espaco_page():
    return render_template("espaco.html", form_data={})


@main_bp.route("/listar-espacos")
@login_required
def listar_espacos_page():
    return redirect(url_for("espaco.listar_espacos"))


@main_bp.route("/listar-utilizadores")
@admin_required
def listar_utilizadores():
    users = User.query.filter_by(isAdmin=False).order_by(User.nome.asc()).all()
    total_ativos = sum(1 for user in users if user.estado == EstadoUser.ativo)
    total_inativos = len(users) - total_ativos

    return render_template(
        "listar_utilizadores.html",
        users=users,
        total_ativos=total_ativos,
        total_inativos=total_inativos,
    )


@main_bp.route("/perfil-utilizador")
@login_required
def perfil_utilizador():
    user = User.query.get(session["user_id"])
    return _render_form_utilizador(user, _dados_form_user(user, {}))


@main_bp.route("/editar-utilizador/<int:user_id>")
@admin_required
def editar_utilizador_page(user_id):
    user = User.query.get_or_404(user_id)
    return _render_form_utilizador(user, _dados_form_user(user, {}))


@main_bp.route("/editar-utilizador/<int:user_id>", methods=["POST"])
@login_required
def editar_utilizador(user_id):
    user = User.query.get_or_404(user_id)

    if not session.get("is_admin") and session["user_id"] != user_id:
        flash("Acesso restrito", "danger")
        return redirect(url_for("main.index"))

    is_self_edit = session["user_id"] == user.id
    nome = request.form.get("nome", "").strip()
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    data_str = request.form.get("dataNascimento", "").strip()
    estado = request.form.get("estado", "").strip()
    nova_password = request.form.get("password", "")

    form_data = {
        "nome": nome,
        "username": username,
        "email": email,
        "dataNascimento": data_str,
        "estado": estado,
    }

    if not nome or not username or not email or not data_str or not estado:
        flash("Todos os campos obrigatorios devem ser preenchidos.", "danger")
        return _render_form_utilizador(user, form_data)

    if estado not in {"ativo", "inativo"}:
        flash("Estado invalido.", "danger")
        return _render_form_utilizador(user, form_data)

    data_nascimento = _parse_data_nascimento(data_str)
    if data_nascimento is None:
        flash("Data de nascimento inválida.", "danger")
        return _render_form_utilizador(user, form_data)

    if data_nascimento > date.today():
        flash("Data de nascimento inválida.", "danger")
        return _render_form_utilizador(user, form_data)

    if _nome_tem_numero(nome):
        flash("O nome não pode conter números.", "danger")
        return _render_form_utilizador(user, form_data)

    if not _tem_idade_minima(data_nascimento):
        flash("É necessário ter pelo menos 16 anos para criar conta.", "danger")
        return _render_form_utilizador(user, form_data)

    if not _email_valido(email):
        flash("Email invalido.", "danger")
        return _render_form_utilizador(user, form_data)

    existe_username = User.query.filter(User.username == username, User.id != user.id).first()
    if existe_username:
        flash("Username ja existe.", "danger")
        return _render_form_utilizador(user, form_data)

    existe_email = User.query.filter(User.email == email, User.id != user.id).first()
    if existe_email:
        flash("Email ja existe.", "danger")
        return _render_form_utilizador(user, form_data)

    if not is_self_edit:
        nova_password = ""

    if nova_password:
        password_error = _validar_password(nova_password)
        if password_error:
            flash(password_error, "danger")
            return _render_form_utilizador(user, form_data)

    estado_atual = user.estado
    novo_estado = _normalizar_estado_user(estado)

    user.nome = nome
    user.username = username
    user.email = email
    user.dataNascimento = data_nascimento

    if nova_password:
        user.password = _hash_password(nova_password)

    if estado_atual != EstadoUser.inativo and novo_estado == EstadoUser.inativo:
        pode_inativar, mensagem = _pode_inativar_conta(user)

        if not pode_inativar:
            db.session.rollback()
            flash(mensagem, "danger")
            return _render_form_utilizador(user, form_data)

    user.estado = novo_estado
    db.session.commit()

    if is_self_edit:
        session["username"] = user.username

    if is_self_edit and user.estado == EstadoUser.inativo:
        session.clear()
        flash("Conta inativada com sucesso.", "success")
        return redirect(url_for("main.index"))

    flash("Utilizador atualizado com sucesso!", "success")

    if session.get("is_admin"):
        return redirect(url_for("main.editar_utilizador_page", user_id=user.id))

    return redirect(url_for("main.perfil_utilizador"))


@main_bp.route("/alterar-estado-utilizador/<int:user_id>", methods=["POST"])
@admin_required
def alterar_estado_utilizador(user_id):
    user = User.query.get_or_404(user_id)
    novo_estado = request.form.get("estado", "").strip()

    if novo_estado not in {"ativo", "inativo"}:
        flash("Estado invalido.", "danger")
        return redirect(url_for("main.listar_utilizadores"))

    estado_enum = _normalizar_estado_user(novo_estado)
    if user.estado == estado_enum:
        return redirect(url_for("main.listar_utilizadores"))

    if estado_enum == EstadoUser.inativo:
        pode_inativar, mensagem = _pode_inativar_conta(user)
        if not pode_inativar:
            db.session.rollback()
            flash(mensagem, "danger")
            return redirect(url_for("main.listar_utilizadores"))

    user.estado = estado_enum
    db.session.commit()

    flash(
        "Conta ativada com sucesso." if user.estado == EstadoUser.ativo else "Conta inativada com sucesso.",
        "success",
    )
    return redirect(url_for("main.listar_utilizadores"))
