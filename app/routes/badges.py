from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.models import BadgeMeta

badges_bp = Blueprint("badges", __name__, url_prefix="/badges")


def moeda_para_float(valor):
    try:
        return float((valor or "0").replace(".", "").replace(",", "."))
    except Exception:
        return None


@badges_bp.route("/")
@login_required
def listar():
    status = request.args.get("status", "").strip()

    query = BadgeMeta.query

    if status:
        query = query.filter(BadgeMeta.status == status)

    badges = query.order_by(BadgeMeta.nome.asc()).all()

    return render_template(
        "badges/listar.html",
        badges=badges,
        status=status
    )


@badges_bp.route("/nova", methods=["GET", "POST"])
@login_required
def nova():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        cor_hex = request.form.get("cor_hex", "").strip()
        valor_manha = request.form.get("valor_manha", "").strip()
        valor_tarde = request.form.get("valor_tarde", "").strip()
        status = request.form.get("status", "ativa").strip()
        observacao = request.form.get("observacao", "").strip()

        if not nome:
            flash("Informe o nome da badge.", "danger")
            return render_template("badges/nova.html")

        if not cor_hex:
            flash("Informe a cor da badge.", "danger")
            return render_template("badges/nova.html")

        valor_manha_float = moeda_para_float(valor_manha)
        valor_tarde_float = moeda_para_float(valor_tarde)

        if valor_manha_float is None:
            flash("Informe um valor válido para a manhã.", "danger")
            return render_template("badges/nova.html")

        if valor_tarde_float is None:
            flash("Informe um valor válido para a tarde.", "danger")
            return render_template("badges/nova.html")

        existente = BadgeMeta.query.filter_by(nome=nome).first()
        if existente:
            flash("Já existe uma badge com esse nome.", "danger")
            return render_template("badges/nova.html")

        badge = BadgeMeta(
            nome=nome,
            cor_hex=cor_hex,
            valor_manha=valor_manha_float,
            valor_tarde=valor_tarde_float,
            status=status if status in ["ativa", "inativa"] else "ativa",
            observacao=observacao or None
        )

        db.session.add(badge)
        db.session.commit()

        flash("Badge cadastrada com sucesso.", "success")
        return redirect(url_for("badges.listar"))

    return render_template("badges/nova.html")


@badges_bp.route("/editar/<int:badge_id>", methods=["GET", "POST"])
@login_required
def editar(badge_id):
    badge = BadgeMeta.query.get_or_404(badge_id)

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        cor_hex = request.form.get("cor_hex", "").strip()
        valor_manha = request.form.get("valor_manha", "").strip()
        valor_tarde = request.form.get("valor_tarde", "").strip()
        status = request.form.get("status", "ativa").strip()
        observacao = request.form.get("observacao", "").strip()

        if not nome:
            flash("Informe o nome da badge.", "danger")
            return render_template("badges/editar.html", badge=badge)

        if not cor_hex:
            flash("Informe a cor da badge.", "danger")
            return render_template("badges/editar.html", badge=badge)

        valor_manha_float = moeda_para_float(valor_manha)
        valor_tarde_float = moeda_para_float(valor_tarde)

        if valor_manha_float is None:
            flash("Informe um valor válido para a manhã.", "danger")
            return render_template("badges/editar.html", badge=badge)

        if valor_tarde_float is None:
            flash("Informe um valor válido para a tarde.", "danger")
            return render_template("badges/editar.html", badge=badge)

        existente = BadgeMeta.query.filter(BadgeMeta.nome == nome, BadgeMeta.id != badge.id).first()
        if existente:
            flash("Já existe outra badge com esse nome.", "danger")
            return render_template("badges/editar.html", badge=badge)

        badge.nome = nome
        badge.cor_hex = cor_hex
        badge.valor_manha = valor_manha_float
        badge.valor_tarde = valor_tarde_float
        badge.status = status if status in ["ativa", "inativa"] else "ativa"
        badge.observacao = observacao or None

        db.session.commit()

        flash("Badge atualizada com sucesso.", "success")
        return redirect(url_for("badges.listar"))

    return render_template("badges/editar.html", badge=badge)