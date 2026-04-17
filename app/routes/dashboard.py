import calendar
from datetime import date

from flask import Blueprint, render_template, request
from flask_login import login_required
from sqlalchemy import extract

from app import db
from app.models import (
    CalendarioVendedora,
    ConfiguracaoDia,
    EscalaVendedora,
    Farmacia,
    Feriado,
    Vendedora
)

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def nome_dia_semana_pt(data_obj):
    dias = {
        0: "segunda",
        1: "terca",
        2: "quarta",
        3: "quinta",
        4: "sexta",
        5: "sabado",
        6: "domingo",
    }
    return dias.get(data_obj.weekday(), "")


def tipo_dia_da_data(data_obj, feriados_map):
    if data_obj in feriados_map:
        return "feriado"
    return nome_dia_semana_pt(data_obj)


@dashboard_bp.route("/")
@login_required
def index():
    hoje = date.today()
    mes = request.args.get("mes", type=int) or hoje.month
    ano = request.args.get("ano", type=int) or hoje.year
    farmacia_id = request.args.get("farmacia_id", type=int)

    farmacias = Farmacia.query.order_by(Farmacia.nome.asc()).all()

    total_farmacias = Farmacia.query.count()
    total_vendedoras = Vendedora.query.count()
    total_badges_configuradas = ConfiguracaoDia.query.count()
    total_escalas = EscalaVendedora.query.count()

    farmacia_atual = None
    escalas_hoje = []
    painel_hoje = []
    calendario_resumo = []

    resumo_vendedoras_mes = []
    detalhes_vendedoras_mes = []

    total_meta_mensal_vendedoras = 0.0
    total_dias_trabalhados_mes = 0

    if farmacia_id:
        farmacia_atual = Farmacia.query.get(farmacia_id)

        escalas_fixas = EscalaVendedora.query.filter_by(
            farmacia_id=farmacia_id,
            status="ativa"
        ).all()

        calendarios_mes = CalendarioVendedora.query.filter(
            CalendarioVendedora.farmacia_id == farmacia_id,
            extract("month", CalendarioVendedora.data) == mes,
            extract("year", CalendarioVendedora.data) == ano
        ).all()

        feriados_mes = Feriado.query.filter(
            Feriado.farmacia_id == farmacia_id,
            extract("month", Feriado.data) == mes,
            extract("year", Feriado.data) == ano
        ).all()

        configuracoes = ConfiguracaoDia.query.filter_by(
            farmacia_id=farmacia_id
        ).all()

        mapa_feriados = {f.data: f for f in feriados_mes}
        mapa_config = {c.tipo_dia: c for c in configuracoes}
        mapa_turnos_fixos = {e.vendedora_id: e.turno for e in escalas_fixas}
        mapa_vendedoras = {e.vendedora_id: e.vendedora for e in escalas_fixas}
        mapa_calendario = {(c.vendedora_id, c.data): c for c in calendarios_mes}

        # =========================
        # PAINEL DE HOJE
        # =========================
        tipo_hoje = tipo_dia_da_data(hoje, mapa_feriados)
        config_hoje = mapa_config.get(tipo_hoje)

        vendedoras_hoje = []
        for vendedora_id, turno_fixo in mapa_turnos_fixos.items():
            registro = mapa_calendario.get((vendedora_id, hoje))
            if registro and registro.trabalha:
                turno_real = registro.turno_dia if registro.turno_dia in ["manha", "tarde"] else turno_fixo
                vendedoras_hoje.append({
                    "vendedora": mapa_vendedoras[vendedora_id],
                    "turno": turno_real
                })

        qtd_manha = sum(1 for item in vendedoras_hoje if item["turno"] == "manha")
        qtd_tarde = sum(1 for item in vendedoras_hoje if item["turno"] == "tarde")

        if config_hoje:
            meta_manha = float(config_hoje.badge.valor_manha or 0)
            meta_tarde = float(config_hoje.badge.valor_tarde or 0)

            meta_individual_manha = meta_manha / qtd_manha if qtd_manha > 0 else 0
            meta_individual_tarde = meta_tarde / qtd_tarde if qtd_tarde > 0 else 0

            escalas_hoje.append({
                "tipo_dia": tipo_hoje,
                "badge_nome": config_hoje.badge.nome,
                "badge_cor": config_hoje.badge.cor_hex,
                "valor_manha": meta_manha,
                "valor_tarde": meta_tarde,
                "qtd_manha": qtd_manha,
                "qtd_tarde": qtd_tarde,
                "meta_individual_manha": meta_individual_manha,
                "meta_individual_tarde": meta_individual_tarde,
                "feriado_descricao": mapa_feriados.get(hoje).descricao if hoje in mapa_feriados else None
            })

            for item in vendedoras_hoje:
                if item["turno"] == "manha":
                    meta_individual = meta_individual_manha
                    valor_turno = meta_manha
                    qtd_turno = qtd_manha
                else:
                    meta_individual = meta_individual_tarde
                    valor_turno = meta_tarde
                    qtd_turno = qtd_tarde

                painel_hoje.append({
                    "nome": item["vendedora"].nome,
                    "turno": item["turno"],
                    "badge_nome": config_hoje.badge.nome,
                    "badge_cor": config_hoje.badge.cor_hex,
                    "valor_turno": valor_turno,
                    "qtd_turno": qtd_turno,
                    "meta_individual": meta_individual
                })

        # =========================
        # RESUMO DO MÊS
        # =========================
        total_dias = calendar.monthrange(ano, mes)[1]
        acumulado_vendedoras = {}

        for dia in range(1, total_dias + 1):
            data_ref = date(ano, mes, dia)
            tipo_dia = tipo_dia_da_data(data_ref, mapa_feriados)
            config = mapa_config.get(tipo_dia)

            trabalhando = []
            for vendedora_id, turno_fixo in mapa_turnos_fixos.items():
                registro = mapa_calendario.get((vendedora_id, data_ref))
                if registro and registro.trabalha:
                    turno_real = registro.turno_dia if registro.turno_dia in ["manha", "tarde"] else turno_fixo
                    trabalhando.append({
                        "vendedora_id": vendedora_id,
                        "vendedora": mapa_vendedoras[vendedora_id],
                        "turno": turno_real
                    })

            qtd_manha = sum(1 for item in trabalhando if item["turno"] == "manha")
            qtd_tarde = sum(1 for item in trabalhando if item["turno"] == "tarde")

            valor_manha = float(config.badge.valor_manha or 0) if config else 0
            valor_tarde = float(config.badge.valor_tarde or 0) if config else 0

            meta_individual_manha = (valor_manha / qtd_manha) if qtd_manha > 0 else 0
            meta_individual_tarde = (valor_tarde / qtd_tarde) if qtd_tarde > 0 else 0

            calendario_resumo.append({
                "data": data_ref,
                "tipo_dia": tipo_dia,
                "feriado_descricao": mapa_feriados.get(data_ref).descricao if data_ref in mapa_feriados else None,
                "badge_nome": config.badge.nome if config else "-",
                "badge_cor": config.badge.cor_hex if config else "#94a3b8",
                "valor_manha": valor_manha,
                "valor_tarde": valor_tarde,
                "qtd_manha": qtd_manha,
                "qtd_tarde": qtd_tarde,
                "meta_individual_manha": meta_individual_manha,
                "meta_individual_tarde": meta_individual_tarde
            })

            for item in trabalhando:
                if item["turno"] == "manha":
                    meta_individual = meta_individual_manha
                else:
                    meta_individual = meta_individual_tarde

                vendedora_id = item["vendedora_id"]

                if vendedora_id not in acumulado_vendedoras:
                    acumulado_vendedoras[vendedora_id] = {
                        "nome": item["vendedora"].nome,
                        "turno": item["turno"],
                        "dias_trabalhados": 0,
                        "meta_total": 0.0
                    }

                acumulado_vendedoras[vendedora_id]["dias_trabalhados"] += 1
                acumulado_vendedoras[vendedora_id]["meta_total"] += meta_individual

                detalhes_vendedoras_mes.append({
                    "data": data_ref,
                    "vendedora_nome": item["vendedora"].nome,
                    "turno": item["turno"],
                    "tipo_dia": tipo_dia,
                    "badge_nome": config.badge.nome if config else "-",
                    "badge_cor": config.badge.cor_hex if config else "#94a3b8",
                    "meta_individual": meta_individual,
                    "feriado_descricao": mapa_feriados.get(data_ref).descricao if data_ref in mapa_feriados else None
                })

        resumo_vendedoras_mes = sorted(
            list(acumulado_vendedoras.values()),
            key=lambda x: x["meta_total"],
            reverse=True
        )

        total_meta_mensal_vendedoras = sum(item["meta_total"] for item in resumo_vendedoras_mes)
        total_dias_trabalhados_mes = sum(item["dias_trabalhados"] for item in resumo_vendedoras_mes)

        detalhes_vendedoras_mes = sorted(
            detalhes_vendedoras_mes,
            key=lambda x: (x["data"], x["vendedora_nome"])
        )

    return render_template(
        "dashboard.html",
        hoje=hoje,
        mes=mes,
        ano=ano,
        farmacias=farmacias,
        farmacia_id=farmacia_id,
        farmacia_atual=farmacia_atual,
        total_farmacias=total_farmacias,
        total_vendedoras=total_vendedoras,
        total_badges_configuradas=total_badges_configuradas,
        total_escalas=total_escalas,
        escalas_hoje=escalas_hoje,
        painel_hoje=painel_hoje,
        calendario_resumo=calendario_resumo,
        resumo_vendedoras_mes=resumo_vendedoras_mes,
        detalhes_vendedoras_mes=detalhes_vendedoras_mes,
        total_meta_mensal_vendedoras=total_meta_mensal_vendedoras,
        total_dias_trabalhados_mes=total_dias_trabalhados_mes
    )