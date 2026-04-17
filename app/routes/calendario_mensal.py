import calendar
from datetime import date, datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import extract

from app import db
from app.models import CalendarioVendedora, EscalaVendedora, Farmacia, Feriado, Vendedora

calendario_mensal_bp = Blueprint("calendario_mensal", __name__, url_prefix="/calendario-mensal")


@calendario_mensal_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    hoje = date.today()
    mes = request.args.get("mes", type=int) or hoje.month
    ano = request.args.get("ano", type=int) or hoje.year
    farmacia_id = request.args.get("farmacia_id", type=int)
    vendedora_id = request.args.get("vendedora_id", type=int)

    farmacias = Farmacia.query.order_by(Farmacia.nome.asc()).all()
    vendedoras = []
    turno_fixo = None

    if farmacia_id:
        vendedoras = (
            Vendedora.query
            .filter_by(farmacia_id=farmacia_id, status="ativa")
            .order_by(Vendedora.nome.asc())
            .all()
        )

    if request.method == "POST":
        farmacia_id = request.form.get("farmacia_id", type=int)
        vendedora_id = request.form.get("vendedora_id", type=int)
        mes = request.form.get("mes", type=int)
        ano = request.form.get("ano", type=int)
        data_str = request.form.get("data", "").strip()
        acao = request.form.get("acao", "").strip()
        turno_dia = request.form.get("turno_dia", "fixo").strip()

        if not farmacia_id:
            flash("Selecione a farmácia.", "danger")
            return redirect(url_for("calendario_mensal.index", mes=mes, ano=ano))

        if not vendedora_id:
            flash("Selecione a vendedora.", "danger")
            return redirect(url_for("calendario_mensal.index", farmacia_id=farmacia_id, mes=mes, ano=ano))

        if not data_str:
            flash("Data inválida.", "danger")
            return redirect(url_for("calendario_mensal.index", farmacia_id=farmacia_id, vendedora_id=vendedora_id, mes=mes, ano=ano))

        if turno_dia not in ["fixo", "manha", "tarde"]:
            turno_dia = "fixo"

        try:
            data_ref = datetime.strptime(data_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Data inválida.", "danger")
            return redirect(url_for("calendario_mensal.index", farmacia_id=farmacia_id, vendedora_id=vendedora_id, mes=mes, ano=ano))

        registro = CalendarioVendedora.query.filter_by(
            farmacia_id=farmacia_id,
            vendedora_id=vendedora_id,
            data=data_ref
        ).first()

        if acao == "trabalha":
            if registro:
                registro.trabalha = True
                registro.turno_dia = turno_dia
            else:
                registro = CalendarioVendedora(
                    farmacia_id=farmacia_id,
                    vendedora_id=vendedora_id,
                    data=data_ref,
                    trabalha=True,
                    turno_dia=turno_dia
                )
                db.session.add(registro)
            flash(f"Dia {data_ref.strftime('%d/%m/%Y')} marcado como trabalha.", "success")

        elif acao == "folga":
            if registro:
                registro.trabalha = False
                registro.turno_dia = turno_dia
            else:
                registro = CalendarioVendedora(
                    farmacia_id=farmacia_id,
                    vendedora_id=vendedora_id,
                    data=data_ref,
                    trabalha=False,
                    turno_dia=turno_dia
                )
                db.session.add(registro)
            flash(f"Dia {data_ref.strftime('%d/%m/%Y')} marcado como folga.", "warning")

        elif acao == "limpar":
            if registro:
                db.session.delete(registro)
                flash(f"Dia {data_ref.strftime('%d/%m/%Y')} limpo com sucesso.", "info")
            else:
                flash("Esse dia já estava sem marcação.", "info")

        else:
            flash("Ação inválida.", "danger")

        db.session.commit()

        return redirect(
            url_for(
                "calendario_mensal.index",
                farmacia_id=farmacia_id,
                vendedora_id=vendedora_id,
                mes=mes,
                ano=ano
            )
        )

    registros = []
    mapa_registros = {}
    mapa_feriados = {}
    semanas = []

    if farmacia_id and vendedora_id:
        escala = EscalaVendedora.query.filter_by(
            farmacia_id=farmacia_id,
            vendedora_id=vendedora_id
        ).first()

        if escala:
            turno_fixo = escala.turno

        registros = (
            CalendarioVendedora.query
            .filter(
                CalendarioVendedora.farmacia_id == farmacia_id,
                CalendarioVendedora.vendedora_id == vendedora_id,
                extract("month", CalendarioVendedora.data) == mes,
                extract("year", CalendarioVendedora.data) == ano
            )
            .all()
        )
        mapa_registros = {r.data: r for r in registros}

        feriados = (
            Feriado.query
            .filter(
                Feriado.farmacia_id == farmacia_id,
                extract("month", Feriado.data) == mes,
                extract("year", Feriado.data) == ano
            )
            .all()
        )
        mapa_feriados = {f.data: f for f in feriados}

        cal = calendar.Calendar(firstweekday=6)
        semanas = cal.monthdatescalendar(ano, mes)

    return render_template(
        "calendario_mensal/index.html",
        farmacias=farmacias,
        vendedoras=vendedoras,
        farmacia_id=farmacia_id,
        vendedora_id=vendedora_id,
        mes=mes,
        ano=ano,
        turno_fixo=turno_fixo,
        mapa_registros=mapa_registros,
        mapa_feriados=mapa_feriados,
        semanas=semanas
    )