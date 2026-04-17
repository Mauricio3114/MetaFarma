from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.models import Feriado, Farmacia

feriados_bp = Blueprint("feriados", __name__, url_prefix="/feriados")


@feriados_bp.route("/")
@login_required
def listar():
    farmacia_id = request.args.get("farmacia_id", type=int)

    query = Feriado.query.join(Farmacia)
    if farmacia_id:
        query = query.filter(Feriado.farmacia_id == farmacia_id)

    feriados = query.order_by(Feriado.data.asc()).all()
    farmacias = Farmacia.query.order_by(Farmacia.nome.asc()).all()

    return render_template(
        "feriados/listar.html",
        feriados=feriados,
        farmacias=farmacias,
        farmacia_id=farmacia_id
    )


@feriados_bp.route("/novo", methods=["GET", "POST"])
@login_required
def novo():
    farmacias = Farmacia.query.filter_by(status="ativa").order_by(Farmacia.nome.asc()).all()

    if request.method == "POST":
        farmacia_id = request.form.get("farmacia_id", type=int)
        data_str = request.form.get("data", "").strip()
        descricao = request.form.get("descricao", "").strip()

        if not farmacia_id:
            flash("Selecione a farmácia.", "danger")
            return render_template("feriados/novo.html", farmacias=farmacias)

        if not data_str:
            flash("Informe a data do feriado.", "danger")
            return render_template("feriados/novo.html", farmacias=farmacias)

        if not descricao:
            flash("Informe a descrição do feriado.", "danger")
            return render_template("feriados/novo.html", farmacias=farmacias)

        try:
            data = datetime.strptime(data_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Data inválida.", "danger")
            return render_template("feriados/novo.html", farmacias=farmacias)

        existente = Feriado.query.filter_by(farmacia_id=farmacia_id, data=data).first()
        if existente:
            flash("Já existe um feriado cadastrado nessa data para essa farmácia.", "danger")
            return render_template("feriados/novo.html", farmacias=farmacias)

        novo_feriado = Feriado(
            farmacia_id=farmacia_id,
            data=data,
            descricao=descricao
        )
        db.session.add(novo_feriado)
        db.session.commit()

        flash("Feriado cadastrado com sucesso.", "success")
        return redirect(url_for("feriados.listar"))

    return render_template("feriados/novo.html", farmacias=farmacias)