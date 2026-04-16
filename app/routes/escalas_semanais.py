from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.models import BadgeMeta, EscalaSemanal, Farmacia

escalas_semanais_bp = Blueprint("escalas_semanais", __name__, url_prefix="/escalas-semanais")

DIAS_SEMANA = [
    "segunda",
    "terca",
    "quarta",
    "quinta",
    "sexta",
    "sabado",
    "domingo",
]


@escalas_semanais_bp.route("/")
@login_required
def listar():
    farmacia_id = request.args.get("farmacia_id", type=int)

    query = EscalaSemanal.query.join(Farmacia).join(BadgeMeta)

    if farmacia_id:
        query = query.filter(EscalaSemanal.farmacia_id == farmacia_id)

    escalas = query.order_by(EscalaSemanal.farmacia_id.asc(), EscalaSemanal.id.asc()).all()
    farmacias = Farmacia.query.order_by(Farmacia.nome.asc()).all()

    return render_template(
        "escalas_semanais/listar.html",
        escalas=escalas,
        farmacias=farmacias,
        farmacia_id=farmacia_id,
        dias_semana=DIAS_SEMANA
    )


@escalas_semanais_bp.route("/nova", methods=["GET", "POST"])
@login_required
def nova():
    farmacias = Farmacia.query.filter_by(status="ativa").order_by(Farmacia.nome.asc()).all()
    badges = BadgeMeta.query.filter_by(status="ativa").order_by(BadgeMeta.nome.asc()).all()

    if not farmacias:
        flash("Cadastre pelo menos uma farmácia antes de montar a escala semanal.", "warning")
        return redirect(url_for("farmacias.nova"))

    if not badges:
        flash("Cadastre pelo menos uma badge antes de montar a escala semanal.", "warning")
        return redirect(url_for("badges.nova"))

    if request.method == "POST":
        farmacia_id = request.form.get("farmacia_id", type=int)
        dia_semana = request.form.get("dia_semana", "").strip()
        badge_id = request.form.get("badge_id", type=int)
        quantidade_manha = request.form.get("quantidade_manha", "0").strip()
        quantidade_tarde = request.form.get("quantidade_tarde", "0").strip()
        observacao = request.form.get("observacao", "").strip()

        if not farmacia_id:
            flash("Selecione a farmácia.", "danger")
            return render_template("escalas_semanais/nova.html", farmacias=farmacias, badges=badges, dias_semana=DIAS_SEMANA)

        if dia_semana not in DIAS_SEMANA:
            flash("Selecione um dia da semana válido.", "danger")
            return render_template("escalas_semanais/nova.html", farmacias=farmacias, badges=badges, dias_semana=DIAS_SEMANA)

        if not badge_id:
            flash("Selecione a badge.", "danger")
            return render_template("escalas_semanais/nova.html", farmacias=farmacias, badges=badges, dias_semana=DIAS_SEMANA)

        try:
            qtd_manha_int = int(quantidade_manha or 0)
            qtd_tarde_int = int(quantidade_tarde or 0)
        except ValueError:
            flash("Informe quantidades válidas para manhã e tarde.", "danger")
            return render_template("escalas_semanais/nova.html", farmacias=farmacias, badges=badges, dias_semana=DIAS_SEMANA)

        existente = EscalaSemanal.query.filter_by(
            farmacia_id=farmacia_id,
            dia_semana=dia_semana
        ).first()

        if existente:
            flash("Já existe uma escala para esse dia nessa farmácia. Edite a existente.", "danger")
            return render_template("escalas_semanais/nova.html", farmacias=farmacias, badges=badges, dias_semana=DIAS_SEMANA)

        escala = EscalaSemanal(
            farmacia_id=farmacia_id,
            dia_semana=dia_semana,
            badge_id=badge_id,
            quantidade_manha=qtd_manha_int,
            quantidade_tarde=qtd_tarde_int,
            observacao=observacao or None
        )

        db.session.add(escala)
        db.session.commit()

        flash("Escala semanal cadastrada com sucesso.", "success")
        return redirect(url_for("escalas_semanais.listar"))

    return render_template("escalas_semanais/nova.html", farmacias=farmacias, badges=badges, dias_semana=DIAS_SEMANA)


@escalas_semanais_bp.route("/editar/<int:escala_id>", methods=["GET", "POST"])
@login_required
def editar(escala_id):
    escala = EscalaSemanal.query.get_or_404(escala_id)
    farmacias = Farmacia.query.filter_by(status="ativa").order_by(Farmacia.nome.asc()).all()
    badges = BadgeMeta.query.filter_by(status="ativa").order_by(BadgeMeta.nome.asc()).all()

    if request.method == "POST":
        farmacia_id = request.form.get("farmacia_id", type=int)
        dia_semana = request.form.get("dia_semana", "").strip()
        badge_id = request.form.get("badge_id", type=int)
        quantidade_manha = request.form.get("quantidade_manha", "0").strip()
        quantidade_tarde = request.form.get("quantidade_tarde", "0").strip()
        observacao = request.form.get("observacao", "").strip()

        if not farmacia_id:
            flash("Selecione a farmácia.", "danger")
            return render_template("escalas_semanais/editar.html", escala=escala, farmacias=farmacias, badges=badges, dias_semana=DIAS_SEMANA)

        if dia_semana not in DIAS_SEMANA:
            flash("Selecione um dia da semana válido.", "danger")
            return render_template("escalas_semanais/editar.html", escala=escala, farmacias=farmacias, badges=badges, dias_semana=DIAS_SEMANA)

        if not badge_id:
            flash("Selecione a badge.", "danger")
            return render_template("escalas_semanais/editar.html", escala=escala, farmacias=farmacias, badges=badges, dias_semana=DIAS_SEMANA)

        try:
            qtd_manha_int = int(quantidade_manha or 0)
            qtd_tarde_int = int(quantidade_tarde or 0)
        except ValueError:
            flash("Informe quantidades válidas para manhã e tarde.", "danger")
            return render_template("escalas_semanais/editar.html", escala=escala, farmacias=farmacias, badges=badges, dias_semana=DIAS_SEMANA)

        existente = EscalaSemanal.query.filter(
            EscalaSemanal.farmacia_id == farmacia_id,
            EscalaSemanal.dia_semana == dia_semana,
            EscalaSemanal.id != escala.id
        ).first()

        if existente:
            flash("Já existe outra escala para esse dia nessa farmácia.", "danger")
            return render_template("escalas_semanais/editar.html", escala=escala, farmacias=farmacias, badges=badges, dias_semana=DIAS_SEMANA)

        escala.farmacia_id = farmacia_id
        escala.dia_semana = dia_semana
        escala.badge_id = badge_id
        escala.quantidade_manha = qtd_manha_int
        escala.quantidade_tarde = qtd_tarde_int
        escala.observacao = observacao or None

        db.session.commit()

        flash("Escala semanal atualizada com sucesso.", "success")
        return redirect(url_for("escalas_semanais.listar"))

    return render_template("escalas_semanais/editar.html", escala=escala, farmacias=farmacias, badges=badges, dias_semana=DIAS_SEMANA)