from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.models import Farmacia, Vendedora

vendedoras_bp = Blueprint("vendedoras", __name__, url_prefix="/vendedoras")


@vendedoras_bp.route("/")
@login_required
def listar():
    farmacia_id = request.args.get("farmacia_id", type=int)
    status = request.args.get("status", "").strip()

    query = Vendedora.query.join(Farmacia)

    if farmacia_id:
        query = query.filter(Vendedora.farmacia_id == farmacia_id)

    if status:
        query = query.filter(Vendedora.status == status)

    vendedoras = query.order_by(Vendedora.nome.asc()).all()
    farmacias = Farmacia.query.order_by(Farmacia.nome.asc()).all()

    return render_template(
        "vendedoras/listar.html",
        vendedoras=vendedoras,
        farmacias=farmacias,
        farmacia_id=farmacia_id,
        status=status
    )


@vendedoras_bp.route("/nova", methods=["GET", "POST"])
@login_required
def nova():
    farmacias = Farmacia.query.filter_by(status="ativa").order_by(Farmacia.nome.asc()).all()

    if not farmacias:
        flash("Cadastre pelo menos uma farmácia antes de cadastrar vendedoras.", "warning")
        return redirect(url_for("farmacias.nova"))

    if request.method == "POST":
        farmacia_id = request.form.get("farmacia_id", type=int)
        nome = request.form.get("nome", "").strip()
        telefone = request.form.get("telefone", "").strip()
        status = request.form.get("status", "ativa").strip()
        observacao = request.form.get("observacao", "").strip()

        if not farmacia_id:
            flash("Selecione a farmácia.", "danger")
            return render_template("vendedoras/nova.html", farmacias=farmacias)

        if not nome:
            flash("Informe o nome da vendedora.", "danger")
            return render_template("vendedoras/nova.html", farmacias=farmacias)

        vendedora = Vendedora(
            farmacia_id=farmacia_id,
            nome=nome,
            telefone=telefone or None,
            status=status if status in ["ativa", "inativa"] else "ativa",
            observacao=observacao or None
        )

        db.session.add(vendedora)
        db.session.commit()

        flash("Vendedora cadastrada com sucesso.", "success")
        return redirect(url_for("vendedoras.listar"))

    return render_template("vendedoras/nova.html", farmacias=farmacias)


@vendedoras_bp.route("/editar/<int:vendedora_id>", methods=["GET", "POST"])
@login_required
def editar(vendedora_id):
    vendedora = Vendedora.query.get_or_404(vendedora_id)
    farmacias = Farmacia.query.filter_by(status="ativa").order_by(Farmacia.nome.asc()).all()

    if request.method == "POST":
        farmacia_id = request.form.get("farmacia_id", type=int)
        nome = request.form.get("nome", "").strip()
        telefone = request.form.get("telefone", "").strip()
        status = request.form.get("status", "ativa").strip()
        observacao = request.form.get("observacao", "").strip()

        if not farmacia_id:
            flash("Selecione a farmácia.", "danger")
            return render_template("vendedoras/editar.html", vendedora=vendedora, farmacias=farmacias)

        if not nome:
            flash("Informe o nome da vendedora.", "danger")
            return render_template("vendedoras/editar.html", vendedora=vendedora, farmacias=farmacias)

        vendedora.farmacia_id = farmacia_id
        vendedora.nome = nome
        vendedora.telefone = telefone or None
        vendedora.status = status if status in ["ativa", "inativa"] else "ativa"
        vendedora.observacao = observacao or None

        db.session.commit()

        flash("Vendedora atualizada com sucesso.", "success")
        return redirect(url_for("vendedoras.listar"))

    return render_template("vendedoras/editar.html", vendedora=vendedora, farmacias=farmacias)