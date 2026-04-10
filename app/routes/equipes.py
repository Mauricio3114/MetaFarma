from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.models import Equipe, Farmacia

equipes_bp = Blueprint("equipes", __name__, url_prefix="/equipes")


@equipes_bp.route("/")
@login_required
def listar():
    farmacia_id = request.args.get("farmacia_id", type=int)
    turno = request.args.get("turno", "").strip()
    status = request.args.get("status", "").strip()

    query = Equipe.query.join(Farmacia)

    if farmacia_id:
        query = query.filter(Equipe.farmacia_id == farmacia_id)

    if turno:
        query = query.filter(Equipe.turno == turno)

    if status:
        query = query.filter(Equipe.status == status)

    equipes = query.order_by(Equipe.id.desc()).all()
    farmacias = Farmacia.query.order_by(Farmacia.nome.asc()).all()

    return render_template(
        "equipes/listar.html",
        equipes=equipes,
        farmacias=farmacias,
        farmacia_id=farmacia_id,
        turno=turno,
        status=status
    )


@equipes_bp.route("/nova", methods=["GET", "POST"])
@login_required
def nova():
    farmacias = Farmacia.query.order_by(Farmacia.nome.asc()).all()

    if not farmacias:
        flash("Cadastre pelo menos uma farmácia antes de criar equipes.", "warning")
        return redirect(url_for("farmacias.nova"))

    if request.method == "POST":
        farmacia_id = request.form.get("farmacia_id", type=int)
        nome = request.form.get("nome", "").strip()
        turno = request.form.get("turno", "").strip()
        responsavel = request.form.get("responsavel", "").strip()
        status = request.form.get("status", "ativa").strip()
        observacao = request.form.get("observacao", "").strip()

        if not farmacia_id:
            flash("Selecione a farmácia.", "danger")
            return render_template("equipes/nova.html", farmacias=farmacias)

        if not nome:
            flash("Informe o nome da equipe.", "danger")
            return render_template("equipes/nova.html", farmacias=farmacias)

        if turno not in ["turno1", "turno2"]:
            flash("Selecione um turno válido.", "danger")
            return render_template("equipes/nova.html", farmacias=farmacias)

        if status not in ["ativa", "inativa"]:
            status = "ativa"

        equipe = Equipe(
            farmacia_id=farmacia_id,
            nome=nome,
            turno=turno,
            responsavel=responsavel or None,
            status=status,
            observacao=observacao or None
        )

        db.session.add(equipe)
        db.session.commit()

        flash("Equipe cadastrada com sucesso.", "success")
        return redirect(url_for("equipes.listar"))

    return render_template("equipes/nova.html", farmacias=farmacias)


@equipes_bp.route("/editar/<int:equipe_id>", methods=["GET", "POST"])
@login_required
def editar(equipe_id):
    equipe = Equipe.query.get_or_404(equipe_id)
    farmacias = Farmacia.query.order_by(Farmacia.nome.asc()).all()

    if request.method == "POST":
        farmacia_id = request.form.get("farmacia_id", type=int)
        nome = request.form.get("nome", "").strip()
        turno = request.form.get("turno", "").strip()
        responsavel = request.form.get("responsavel", "").strip()
        status = request.form.get("status", "ativa").strip()
        observacao = request.form.get("observacao", "").strip()

        if not farmacia_id:
            flash("Selecione a farmácia.", "danger")
            return render_template("equipes/editar.html", equipe=equipe, farmacias=farmacias)

        if not nome:
            flash("Informe o nome da equipe.", "danger")
            return render_template("equipes/editar.html", equipe=equipe, farmacias=farmacias)

        if turno not in ["turno1", "turno2"]:
            flash("Selecione um turno válido.", "danger")
            return render_template("equipes/editar.html", equipe=equipe, farmacias=farmacias)

        if status not in ["ativa", "inativa"]:
            status = "ativa"

        equipe.farmacia_id = farmacia_id
        equipe.nome = nome
        equipe.turno = turno
        equipe.responsavel = responsavel or None
        equipe.status = status
        equipe.observacao = observacao or None

        db.session.commit()

        flash("Equipe atualizada com sucesso.", "success")
        return redirect(url_for("equipes.listar"))

    return render_template("equipes/editar.html", equipe=equipe, farmacias=farmacias)