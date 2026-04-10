from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.models import Farmacia

farmacias_bp = Blueprint("farmacias", __name__, url_prefix="/farmacias")


@farmacias_bp.route("/")
@login_required
def listar():
    busca = request.args.get("busca", "").strip()

    query = Farmacia.query

    if busca:
        query = query.filter(Farmacia.nome.ilike(f"%{busca}%"))

    farmacias = query.order_by(Farmacia.nome.asc()).all()

    return render_template("farmacias/listar.html", farmacias=farmacias, busca=busca)


@farmacias_bp.route("/nova", methods=["GET", "POST"])
@login_required
def nova():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        responsavel = request.form.get("responsavel", "").strip()
        cidade = request.form.get("cidade", "").strip()
        telefone = request.form.get("telefone", "").strip()
        status = request.form.get("status", "ativa").strip()
        observacao = request.form.get("observacao", "").strip()

        if not nome:
            flash("O nome da farmácia é obrigatório.", "danger")
            return render_template("farmacias/nova.html")

        farmacia = Farmacia(
            nome=nome,
            responsavel=responsavel or None,
            cidade=cidade or None,
            telefone=telefone or None,
            status=status or "ativa",
            observacao=observacao or None,
        )

        db.session.add(farmacia)
        db.session.commit()

        flash("Farmácia cadastrada com sucesso.", "success")
        return redirect(url_for("farmacias.listar"))

    return render_template("farmacias/nova.html")


@farmacias_bp.route("/editar/<int:farmacia_id>", methods=["GET", "POST"])
@login_required
def editar(farmacia_id):
    farmacia = Farmacia.query.get_or_404(farmacia_id)

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        responsavel = request.form.get("responsavel", "").strip()
        cidade = request.form.get("cidade", "").strip()
        telefone = request.form.get("telefone", "").strip()
        status = request.form.get("status", "ativa").strip()
        observacao = request.form.get("observacao", "").strip()

        if not nome:
            flash("O nome da farmácia é obrigatório.", "danger")
            return render_template("farmacias/editar.html", farmacia=farmacia)

        farmacia.nome = nome
        farmacia.responsavel = responsavel or None
        farmacia.cidade = cidade or None
        farmacia.telefone = telefone or None
        farmacia.status = status or "ativa"
        farmacia.observacao = observacao or None

        db.session.commit()

        flash("Farmácia atualizada com sucesso.", "success")
        return redirect(url_for("farmacias.listar"))

    return render_template("farmacias/editar.html", farmacia=farmacia)