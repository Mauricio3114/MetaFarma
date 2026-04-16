from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.models import EscalaSemanal, EscalaVendedora, Farmacia, Vendedora

escalas_vendedoras_bp = Blueprint("escalas_vendedoras", __name__, url_prefix="/escalas-vendedoras")

DIAS_SEMANA = [
    "segunda",
    "terca",
    "quarta",
    "quinta",
    "sexta",
    "sabado",
    "domingo",
]

TURNOS = ["manha", "tarde"]


@escalas_vendedoras_bp.route("/")
@login_required
def listar():
    farmacia_id = request.args.get("farmacia_id", type=int)
    dia_semana = request.args.get("dia_semana", "").strip()
    turno = request.args.get("turno", "").strip()

    query = EscalaVendedora.query.join(Farmacia).join(Vendedora)

    if farmacia_id:
        query = query.filter(EscalaVendedora.farmacia_id == farmacia_id)

    if dia_semana:
        query = query.filter(EscalaVendedora.dia_semana == dia_semana)

    if turno:
        query = query.filter(EscalaVendedora.turno == turno)

    escalas = query.order_by(
        EscalaVendedora.farmacia_id.asc(),
        EscalaVendedora.dia_semana.asc(),
        EscalaVendedora.turno.asc(),
        EscalaVendedora.id.asc()
    ).all()

    farmacias = Farmacia.query.order_by(Farmacia.nome.asc()).all()

    return render_template(
        "escalas_vendedoras/listar.html",
        escalas=escalas,
        farmacias=farmacias,
        farmacia_id=farmacia_id,
        dia_semana=dia_semana,
        turno=turno,
        dias_semana=DIAS_SEMANA,
        turnos=TURNOS
    )


@escalas_vendedoras_bp.route("/nova", methods=["GET", "POST"])
@login_required
def nova():
    farmacias = Farmacia.query.filter_by(status="ativa").order_by(Farmacia.nome.asc()).all()
    vendedoras = Vendedora.query.filter_by(status="ativa").order_by(Vendedora.nome.asc()).all()

    if not farmacias:
        flash("Cadastre pelo menos uma farmácia antes de montar a escala das vendedoras.", "warning")
        return redirect(url_for("farmacias.nova"))

    if not vendedoras:
        flash("Cadastre pelo menos uma vendedora antes de montar a escala.", "warning")
        return redirect(url_for("vendedoras.nova"))

    if request.method == "POST":
        farmacia_id = request.form.get("farmacia_id", type=int)
        vendedora_id = request.form.get("vendedora_id", type=int)
        dia_semana = request.form.get("dia_semana", "").strip()
        turno = request.form.get("turno", "").strip()
        observacao = request.form.get("observacao", "").strip()

        if not farmacia_id:
            flash("Selecione a farmácia.", "danger")
            return render_template("escalas_vendedoras/nova.html", farmacias=farmacias, vendedoras=vendedoras, dias_semana=DIAS_SEMANA, turnos=TURNOS)

        if not vendedora_id:
            flash("Selecione a vendedora.", "danger")
            return render_template("escalas_vendedoras/nova.html", farmacias=farmacias, vendedoras=vendedoras, dias_semana=DIAS_SEMANA, turnos=TURNOS)

        if dia_semana not in DIAS_SEMANA:
            flash("Selecione um dia da semana válido.", "danger")
            return render_template("escalas_vendedoras/nova.html", farmacias=farmacias, vendedoras=vendedoras, dias_semana=DIAS_SEMANA, turnos=TURNOS)

        if turno not in TURNOS:
            flash("Selecione um turno válido.", "danger")
            return render_template("escalas_vendedoras/nova.html", farmacias=farmacias, vendedoras=vendedoras, dias_semana=DIAS_SEMANA, turnos=TURNOS)

        vendedora = Vendedora.query.get(vendedora_id)
        if not vendedora:
            flash("Vendedora inválida.", "danger")
            return render_template("escalas_vendedoras/nova.html", farmacias=farmacias, vendedoras=vendedoras, dias_semana=DIAS_SEMANA, turnos=TURNOS)

        if vendedora.farmacia_id != farmacia_id:
            flash("A vendedora selecionada não pertence à farmácia escolhida.", "danger")
            return render_template("escalas_vendedoras/nova.html", farmacias=farmacias, vendedoras=vendedoras, dias_semana=DIAS_SEMANA, turnos=TURNOS)

        escala_semana = EscalaSemanal.query.filter_by(
            farmacia_id=farmacia_id,
            dia_semana=dia_semana
        ).first()

        if not escala_semana:
            flash("Primeiro cadastre a escala semanal desse dia para a farmácia.", "danger")
            return render_template("escalas_vendedoras/nova.html", farmacias=farmacias, vendedoras=vendedoras, dias_semana=DIAS_SEMANA, turnos=TURNOS)

        existente = EscalaVendedora.query.filter_by(
            farmacia_id=farmacia_id,
            vendedora_id=vendedora_id,
            dia_semana=dia_semana,
            turno=turno
        ).first()

        if existente:
            flash("Essa vendedora já está cadastrada nesse dia e turno.", "danger")
            return render_template("escalas_vendedoras/nova.html", farmacias=farmacias, vendedoras=vendedoras, dias_semana=DIAS_SEMANA, turnos=TURNOS)

        escala = EscalaVendedora(
            farmacia_id=farmacia_id,
            vendedora_id=vendedora_id,
            dia_semana=dia_semana,
            turno=turno,
            observacao=observacao or None
        )

        db.session.add(escala)
        db.session.commit()

        flash("Escala da vendedora cadastrada com sucesso.", "success")
        return redirect(url_for("escalas_vendedoras.listar"))

    return render_template("escalas_vendedoras/nova.html", farmacias=farmacias, vendedoras=vendedoras, dias_semana=DIAS_SEMANA, turnos=TURNOS)


@escalas_vendedoras_bp.route("/editar/<int:escala_id>", methods=["GET", "POST"])
@login_required
def editar(escala_id):
    escala = EscalaVendedora.query.get_or_404(escala_id)
    farmacias = Farmacia.query.filter_by(status="ativa").order_by(Farmacia.nome.asc()).all()
    vendedoras = Vendedora.query.filter_by(status="ativa").order_by(Vendedora.nome.asc()).all()

    if request.method == "POST":
        farmacia_id = request.form.get("farmacia_id", type=int)
        vendedora_id = request.form.get("vendedora_id", type=int)
        dia_semana = request.form.get("dia_semana", "").strip()
        turno = request.form.get("turno", "").strip()
        observacao = request.form.get("observacao", "").strip()

        if not farmacia_id:
            flash("Selecione a farmácia.", "danger")
            return render_template("escalas_vendedoras/editar.html", escala=escala, farmacias=farmacias, vendedoras=vendedoras, dias_semana=DIAS_SEMANA, turnos=TURNOS)

        if not vendedora_id:
            flash("Selecione a vendedora.", "danger")
            return render_template("escalas_vendedoras/editar.html", escala=escala, farmacias=farmacias, vendedoras=vendedoras, dias_semana=DIAS_SEMANA, turnos=TURNOS)

        if dia_semana not in DIAS_SEMANA:
            flash("Selecione um dia da semana válido.", "danger")
            return render_template("escalas_vendedoras/editar.html", escala=escala, farmacias=farmacias, vendedoras=vendedoras, dias_semana=DIAS_SEMANA, turnos=TURNOS)

        if turno not in TURNOS:
            flash("Selecione um turno válido.", "danger")
            return render_template("escalas_vendedoras/editar.html", escala=escala, farmacias=farmacias, vendedoras=vendedoras, dias_semana=DIAS_SEMANA, turnos=TURNOS)

        vendedora = Vendedora.query.get(vendedora_id)
        if not vendedora:
            flash("Vendedora inválida.", "danger")
            return render_template("escalas_vendedoras/editar.html", escala=escala, farmacias=farmacias, vendedoras=vendedoras, dias_semana=DIAS_SEMANA, turnos=TURNOS)

        if vendedora.farmacia_id != farmacia_id:
            flash("A vendedora selecionada não pertence à farmácia escolhida.", "danger")
            return render_template("escalas_vendedoras/editar.html", escala=escala, farmacias=farmacias, vendedoras=vendedoras, dias_semana=DIAS_SEMANA, turnos=TURNOS)

        escala_semana = EscalaSemanal.query.filter_by(
            farmacia_id=farmacia_id,
            dia_semana=dia_semana
        ).first()

        if not escala_semana:
            flash("Primeiro cadastre a escala semanal desse dia para a farmácia.", "danger")
            return render_template("escalas_vendedoras/editar.html", escala=escala, farmacias=farmacias, vendedoras=vendedoras, dias_semana=DIAS_SEMANA, turnos=TURNOS)

        existente = EscalaVendedora.query.filter(
            EscalaVendedora.farmacia_id == farmacia_id,
            EscalaVendedora.vendedora_id == vendedora_id,
            EscalaVendedora.dia_semana == dia_semana,
            EscalaVendedora.turno == turno,
            EscalaVendedora.id != escala.id
        ).first()

        if existente:
            flash("Já existe essa vendedora nesse dia e turno.", "danger")
            return render_template("escalas_vendedoras/editar.html", escala=escala, farmacias=farmacias, vendedoras=vendedoras, dias_semana=DIAS_SEMANA, turnos=TURNOS)

        escala.farmacia_id = farmacia_id
        escala.vendedora_id = vendedora_id
        escala.dia_semana = dia_semana
        escala.turno = turno
        escala.observacao = observacao or None

        db.session.commit()

        flash("Escala da vendedora atualizada com sucesso.", "success")
        return redirect(url_for("escalas_vendedoras.listar"))

    return render_template("escalas_vendedoras/editar.html", escala=escala, farmacias=farmacias, vendedoras=vendedoras, dias_semana=DIAS_SEMANA, turnos=TURNOS)