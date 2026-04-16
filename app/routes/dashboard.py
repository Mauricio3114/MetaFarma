from datetime import date
from sqlalchemy import func

from flask import Blueprint, render_template
from flask_login import login_required

from app.models import (
    BadgeMeta,
    Equipe,
    EscalaSemanal,
    EscalaVendedora,
    Farmacia,
    Meta,
    Resultado,
    ResultadoVendedora
)

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def safe_float(valor):
    try:
        return float(valor or 0)
    except Exception:
        return 0.0


def calcular_percentual(realizado, meta):
    if meta <= 0:
        return 0
    return round((realizado / meta) * 100, 1)


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


@dashboard_bp.route("/")
@login_required
def index():
    hoje = date.today()
    mes = hoje.month
    ano = hoje.year
    dia_semana_hoje = nome_dia_semana_pt(hoje)

    total_farmacias = Farmacia.query.count()
    farmacias_ativas = Farmacia.query.filter_by(status="ativa").count()
    total_metas = Meta.query.count()
    total_equipes = Equipe.query.count()
    total_resultados = Resultado.query.count()

    total_valor_realizado = safe_float(
        Resultado.query.with_entities(func.sum(Resultado.valor_realizado)).scalar()
    )

    # =========================
    # META DIÁRIA
    # =========================
    meta_diaria = safe_float(
        Meta.query.with_entities(func.sum(Meta.valor_meta))
        .filter(Meta.tipo == "diaria")
        .scalar()
    )

    realizado_dia = safe_float(
        Resultado.query.with_entities(func.sum(Resultado.valor_realizado))
        .filter(Resultado.data_resultado == hoje)
        .scalar()
    )

    perc_dia = calcular_percentual(realizado_dia, meta_diaria)
    falta_dia = max(meta_diaria - realizado_dia, 0)

    # =========================
    # META MENSAL
    # =========================
    meta_mensal = safe_float(
        Meta.query.with_entities(func.sum(Meta.valor_meta))
        .filter(Meta.tipo == "mensal")
        .scalar()
    )

    realizado_mes = safe_float(
        Resultado.query.with_entities(func.sum(Resultado.valor_realizado))
        .filter(func.extract("month", Resultado.data_resultado) == mes)
        .filter(func.extract("year", Resultado.data_resultado) == ano)
        .scalar()
    )

    perc_mes = calcular_percentual(realizado_mes, meta_mensal)
    falta_mes = max(meta_mensal - realizado_mes, 0)

    # =========================
    # META TURNO 1
    # =========================
    meta_turno1 = safe_float(
        Meta.query.with_entities(func.sum(Meta.valor_meta))
        .filter(Meta.tipo == "turno1")
        .filter(Meta.data_inicio <= hoje)
        .filter(Meta.data_fim >= hoje)
        .scalar()
    )

    realizado_turno1 = safe_float(
        Resultado.query.with_entities(func.sum(Resultado.valor_realizado))
        .filter(Resultado.data_resultado == hoje)
        .filter(Resultado.turno == "turno1")
        .scalar()
    )

    perc_turno1 = calcular_percentual(realizado_turno1, meta_turno1)
    falta_turno1 = max(meta_turno1 - realizado_turno1, 0)

    # =========================
    # META TURNO 2
    # =========================
    meta_turno2 = safe_float(
        Meta.query.with_entities(func.sum(Meta.valor_meta))
        .filter(Meta.tipo == "turno2")
        .filter(Meta.data_inicio <= hoje)
        .filter(Meta.data_fim >= hoje)
        .scalar()
    )

    realizado_turno2 = safe_float(
        Resultado.query.with_entities(func.sum(Resultado.valor_realizado))
        .filter(Resultado.data_resultado == hoje)
        .filter(Resultado.turno == "turno2")
        .scalar()
    )

    perc_turno2 = calcular_percentual(realizado_turno2, meta_turno2)
    falta_turno2 = max(meta_turno2 - realizado_turno2, 0)

    # =========================
    # ESCALA DO DIA ATUAL
    # =========================
    escalas_hoje = (
        EscalaSemanal.query
        .join(Farmacia)
        .join(BadgeMeta)
        .filter(EscalaSemanal.dia_semana == dia_semana_hoje)
        .order_by(Farmacia.nome.asc())
        .all()
    )

    # =========================
    # PAINEL VENDEDORAS DO DIA
    # =========================
    painel_vendedoras_hoje = []
    escalas_vendedoras_hoje = (
        EscalaVendedora.query
        .join(Farmacia)
        .filter(EscalaVendedora.dia_semana == dia_semana_hoje)
        .order_by(Farmacia.nome.asc(), EscalaVendedora.turno.asc(), EscalaVendedora.id.asc())
        .all()
    )

    for escala_v in escalas_vendedoras_hoje:
        escala_semana = EscalaSemanal.query.filter_by(
            farmacia_id=escala_v.farmacia_id,
            dia_semana=escala_v.dia_semana
        ).first()

        if not escala_semana:
            continue

        if escala_v.turno == "manha":
            meta_individual = escala_semana.meta_individual_manha()
            valor_turno = float(escala_semana.badge.valor_manha or 0)
            quantidade_turno = int(escala_semana.quantidade_manha or 0)
        else:
            meta_individual = escala_semana.meta_individual_tarde()
            valor_turno = float(escala_semana.badge.valor_tarde or 0)
            quantidade_turno = int(escala_semana.quantidade_tarde or 0)

        painel_vendedoras_hoje.append({
            "farmacia_nome": escala_v.farmacia.nome,
            "vendedora_nome": escala_v.vendedora.nome,
            "dia_semana": escala_v.dia_semana,
            "turno": escala_v.turno,
            "badge_nome": escala_semana.badge.nome,
            "badge_cor": escala_semana.badge.cor_hex,
            "valor_turno": valor_turno,
            "quantidade_turno": quantidade_turno,
            "meta_individual": meta_individual,
        })

    # =========================
    # RESULTADO POR VENDEDORA
    # =========================
    resultados_vendedoras = ResultadoVendedora.query.filter_by(data=hoje).all()

    ranking_vendedoras = []

    for r in resultados_vendedoras:
        escala = EscalaSemanal.query.filter_by(
            farmacia_id=r.farmacia_id,
            dia_semana=dia_semana_hoje
        ).first()

        if not escala:
            continue

        if r.turno == "manha":
            meta = escala.meta_individual_manha()
        else:
            meta = escala.meta_individual_tarde()

        realizado = float(r.valor_realizado or 0)
        percentual = (realizado / meta * 100) if meta > 0 else 0
        falta = max(meta - realizado, 0)

        ranking_vendedoras.append({
            "nome": r.vendedora.nome,
            "farmacia": r.farmacia.nome,
            "turno": r.turno,
            "meta": meta,
            "realizado": realizado,
            "percentual": round(percentual, 1),
            "falta": falta
        })

    ranking_vendedoras = sorted(
        ranking_vendedoras,
        key=lambda x: x["realizado"],
        reverse=True
    )

    # =========================
    # RANKING EQUIPES
    # =========================
    ranking_equipes = (
        Equipe.query
        .join(Resultado, Resultado.equipe_id == Equipe.id)
        .join(Farmacia, Farmacia.id == Equipe.farmacia_id)
        .with_entities(
            Equipe.id,
            Equipe.nome,
            Equipe.turno,
            Farmacia.nome.label("farmacia_nome"),
            func.coalesce(func.sum(Resultado.valor_realizado), 0).label("total_valor"),
            func.coalesce(func.sum(Resultado.pedidos_realizados), 0).label("total_pedidos")
        )
        .group_by(Equipe.id, Equipe.nome, Equipe.turno, Farmacia.nome)
        .order_by(func.coalesce(func.sum(Resultado.valor_realizado), 0).desc())
        .limit(5)
        .all()
    )

    melhor_equipe_dia = (
        Equipe.query
        .join(Resultado, Resultado.equipe_id == Equipe.id)
        .join(Farmacia, Farmacia.id == Equipe.farmacia_id)
        .with_entities(
            Equipe.nome.label("equipe_nome"),
            Equipe.turno.label("turno"),
            Farmacia.nome.label("farmacia_nome"),
            func.coalesce(func.sum(Resultado.valor_realizado), 0).label("total_valor"),
            func.coalesce(func.sum(Resultado.pedidos_realizados), 0).label("total_pedidos")
        )
        .filter(Resultado.data_resultado == hoje)
        .group_by(Equipe.nome, Equipe.turno, Farmacia.nome)
        .order_by(func.coalesce(func.sum(Resultado.valor_realizado), 0).desc())
        .first()
    )

    ranking_farmacias = (
        Farmacia.query
        .outerjoin(Resultado, Resultado.farmacia_id == Farmacia.id)
        .with_entities(
            Farmacia.id,
            Farmacia.nome,
            func.coalesce(func.sum(Resultado.valor_realizado), 0).label("total_valor"),
            func.coalesce(func.sum(Resultado.pedidos_realizados), 0).label("total_pedidos")
        )
        .group_by(Farmacia.id, Farmacia.nome)
        .order_by(func.coalesce(func.sum(Resultado.valor_realizado), 0).desc())
        .limit(5)
        .all()
    )

    melhor_farmacia_dia = (
        Farmacia.query
        .join(Resultado, Resultado.farmacia_id == Farmacia.id)
        .with_entities(
            Farmacia.nome.label("farmacia_nome"),
            func.coalesce(func.sum(Resultado.valor_realizado), 0).label("total_valor"),
            func.coalesce(func.sum(Resultado.pedidos_realizados), 0).label("total_pedidos")
        )
        .filter(Resultado.data_resultado == hoje)
        .group_by(Farmacia.nome)
        .order_by(func.coalesce(func.sum(Resultado.valor_realizado), 0).desc())
        .first()
    )

    pior_desempenho_dia = (
        Equipe.query
        .join(Resultado, Resultado.equipe_id == Equipe.id)
        .join(Farmacia, Farmacia.id == Equipe.farmacia_id)
        .with_entities(
            Equipe.nome.label("equipe_nome"),
            Equipe.turno.label("turno"),
            Farmacia.nome.label("farmacia_nome"),
            func.coalesce(func.sum(Resultado.valor_realizado), 0).label("total_valor"),
            func.coalesce(func.sum(Resultado.pedidos_realizados), 0).label("total_pedidos")
        )
        .filter(Resultado.data_resultado == hoje)
        .group_by(Equipe.nome, Equipe.turno, Farmacia.nome)
        .order_by(func.coalesce(func.sum(Resultado.valor_realizado), 0).asc())
        .first()
    )

    # =========================
    # COMPARATIVO POR FARMÁCIA
    # =========================
    comparativo_farmacias = []
    farmacias = Farmacia.query.order_by(Farmacia.nome.asc()).all()

    for farmacia in farmacias:
        meta_mes_farmacia = safe_float(
            Meta.query.with_entities(func.sum(Meta.valor_meta))
            .filter(Meta.farmacia_id == farmacia.id)
            .filter(Meta.tipo == "mensal")
            .scalar()
        )

        realizado_mes_farmacia = safe_float(
            Resultado.query.with_entities(func.sum(Resultado.valor_realizado))
            .filter(Resultado.farmacia_id == farmacia.id)
            .filter(func.extract("month", Resultado.data_resultado) == mes)
            .filter(func.extract("year", Resultado.data_resultado) == ano)
            .scalar()
        )

        perc_farmacia = calcular_percentual(realizado_mes_farmacia, meta_mes_farmacia)
        falta_farmacia = max(meta_mes_farmacia - realizado_mes_farmacia, 0)

        comparativo_farmacias.append({
            "farmacia_nome": farmacia.nome,
            "meta_mes": meta_mes_farmacia,
            "realizado_mes": realizado_mes_farmacia,
            "percentual": perc_farmacia,
            "falta": falta_farmacia
        })

    comparativo_farmacias = sorted(
        comparativo_farmacias,
        key=lambda x: x["realizado_mes"],
        reverse=True
    )

    # =========================
    # GRÁFICOS
    # =========================
    grafico_turnos_labels = ["Turno 1", "Turno 2"]
    grafico_turnos_meta = [meta_turno1, meta_turno2]
    grafico_turnos_realizado = [realizado_turno1, realizado_turno2]

    grafico_resumo_labels = ["Dia", "Mês"]
    grafico_resumo_meta = [meta_diaria, meta_mensal]
    grafico_resumo_realizado = [realizado_dia, realizado_mes]

    grafico_farmacias_labels = [item["farmacia_nome"] for item in comparativo_farmacias[:6]]
    grafico_farmacias_meta = [item["meta_mes"] for item in comparativo_farmacias[:6]]
    grafico_farmacias_realizado = [item["realizado_mes"] for item in comparativo_farmacias[:6]]

    grafico_pizza_labels = []
    grafico_pizza_valores = []

    for item in comparativo_farmacias[:6]:
        grafico_pizza_labels.append(item["farmacia_nome"] or "Sem nome")
        grafico_pizza_valores.append(float(item["realizado_mes"] or 0))

    ultimos_resultados = (
        Resultado.query
        .order_by(Resultado.data_resultado.desc(), Resultado.id.desc())
        .limit(5)
        .all()
    )

    ultimas_metas = (
        Meta.query
        .order_by(Meta.id.desc())
        .limit(5)
        .all()
    )

    ultimas_equipes = (
        Equipe.query
        .order_by(Equipe.id.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "dashboard.html",
        total_farmacias=total_farmacias,
        farmacias_ativas=farmacias_ativas,
        total_metas=total_metas,
        total_equipes=total_equipes,
        total_resultados=total_resultados,
        total_valor_realizado=total_valor_realizado,

        meta_diaria=meta_diaria,
        realizado_dia=realizado_dia,
        perc_dia=perc_dia,
        falta_dia=falta_dia,

        meta_mensal=meta_mensal,
        realizado_mes=realizado_mes,
        perc_mes=perc_mes,
        falta_mes=falta_mes,

        meta_turno1=meta_turno1,
        realizado_turno1=realizado_turno1,
        perc_turno1=perc_turno1,
        falta_turno1=falta_turno1,

        meta_turno2=meta_turno2,
        realizado_turno2=realizado_turno2,
        perc_turno2=perc_turno2,
        falta_turno2=falta_turno2,

        dia_semana_hoje=dia_semana_hoje,
        escalas_hoje=escalas_hoje,
        painel_vendedoras_hoje=painel_vendedoras_hoje,
        ranking_vendedoras=ranking_vendedoras,

        ranking_equipes=ranking_equipes,
        ranking_farmacias=ranking_farmacias,
        melhor_equipe_dia=melhor_equipe_dia,
        melhor_farmacia_dia=melhor_farmacia_dia,
        pior_desempenho_dia=pior_desempenho_dia,
        comparativo_farmacias=comparativo_farmacias,

        grafico_turnos_labels=grafico_turnos_labels,
        grafico_turnos_meta=grafico_turnos_meta,
        grafico_turnos_realizado=grafico_turnos_realizado,

        grafico_resumo_labels=grafico_resumo_labels,
        grafico_resumo_meta=grafico_resumo_meta,
        grafico_resumo_realizado=grafico_resumo_realizado,

        grafico_farmacias_labels=grafico_farmacias_labels,
        grafico_farmacias_meta=grafico_farmacias_meta,
        grafico_farmacias_realizado=grafico_farmacias_realizado,

        grafico_pizza_labels=grafico_pizza_labels,
        grafico_pizza_valores=grafico_pizza_valores,

        ultimos_resultados=ultimos_resultados,
        ultimas_metas=ultimas_metas,
        ultimas_equipes=ultimas_equipes
    )