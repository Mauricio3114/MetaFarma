from datetime import date, datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.models import Equipe, Farmacia, Resultado

resultados_bp = Blueprint("resultados", __name__, url_prefix="/resultados")


def str_para_data(valor):
    if not valor:
        return None
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except ValueError:
        return None


@resultados_bp.route("/")
@login_required
def listar():
    farmacia_id = request.args.get("farmacia_id", type=int)
    turno = request.args.get("turno", "").strip()
    data_str = request.args.get("data_resultado", "").strip()

    query = Resultado.query.join(Farmacia).join(Equipe)

    if farmacia_id:
        query = query.filter(Resultado.farmacia_id == farmacia_id)

    if turno:
        query = query.filter(Resultado.turno == turno)

    data_resultado = str_para_data(data_str)
    if data_resultado:
        query = query.filter(Resultado.data_resultado == data_resultado)

    resultados = query.order_by(Resultado.data_resultado.desc(), Resultado.id.desc()).all()
    farmacias = Farmacia.query.order_by(Farmacia.nome.asc()).all()

    return render_template(
        "resultados/listar.html",
        resultados=resultados,
        farmacias=farmacias,
        farmacia_id=farmacia_id,
        turno=turno,
        data_resultado=data_str
    )


@resultados_bp.route("/novo", methods=["GET", "POST"])
@login_required
def novo():
    farmacias = Farmacia.query.filter_by(status="ativa").order_by(Farmacia.nome.asc()).all()
    equipes = Equipe.query.filter_by(status="ativa").order_by(Equipe.nome.asc()).all()

    if not farmacias:
        flash("Cadastre pelo menos uma farmácia antes de lançar resultados.", "warning")
        return redirect(url_for("farmacias.nova"))

    if not equipes:
        flash("Cadastre pelo menos uma equipe antes de lançar resultados.", "warning")
        return redirect(url_for("equipes.nova"))

    if request.method == "POST":
        farmacia_id = request.form.get("farmacia_id", type=int)
        equipe_id = request.form.get("equipe_id", type=int)
        data_resultado = str_para_data(request.form.get("data_resultado", "").strip())
        valor_realizado = request.form.get("valor_realizado", "0").strip()
        pedidos_realizados = request.form.get("pedidos_realizados", "0").strip()
        observacao = request.form.get("observacao", "").strip()

        if not farmacia_id:
            flash("Selecione a farmácia.", "danger")
            return render_template("resultados/novo.html", farmacias=farmacias, equipes=equipes, hoje=date.today())

        if not equipe_id:
            flash("Selecione a equipe.", "danger")
            return render_template("resultados/novo.html", farmacias=farmacias, equipes=equipes, hoje=date.today())

        equipe = Equipe.query.get(equipe_id)
        if not equipe:
            flash("Equipe inválida.", "danger")
            return render_template("resultados/novo.html", farmacias=farmacias, equipes=equipes, hoje=date.today())

        if equipe.farmacia_id != farmacia_id:
            flash("A equipe selecionada não pertence à farmácia escolhida.", "danger")
            return render_template("resultados/novo.html", farmacias=farmacias, equipes=equipes, hoje=date.today())

        if not data_resultado:
            data_resultado = date.today()

        try:
            valor_realizado_float = float(valor_realizado.replace(",", ".") or 0)
        except ValueError:
            flash("Informe um valor realizado válido.", "danger")
            return render_template("resultados/novo.html", farmacias=farmacias, equipes=equipes, hoje=date.today())

        try:
            pedidos_realizados_int = int(pedidos_realizados or 0)
        except ValueError:
            flash("Informe uma quantidade de pedidos válida.", "danger")
            return render_template("resultados/novo.html", farmacias=farmacias, equipes=equipes, hoje=date.today())

        resultado = Resultado(
            farmacia_id=farmacia_id,
            equipe_id=equipe_id,
            data_resultado=data_resultado,
            turno=equipe.turno,
            valor_realizado=valor_realizado_float,
            pedidos_realizados=pedidos_realizados_int,
            observacao=observacao or None
        )

        db.session.add(resultado)
        db.session.commit()

        flash("Resultado lançado com sucesso.", "success")
        return redirect(url_for("resultados.listar"))

    return render_template("resultados/novo.html", farmacias=farmacias, equipes=equipes, hoje=date.today())


@resultados_bp.route("/editar/<int:resultado_id>", methods=["GET", "POST"])
@login_required
def editar(resultado_id):
    resultado = Resultado.query.get_or_404(resultado_id)
    farmacias = Farmacia.query.filter_by(status="ativa").order_by(Farmacia.nome.asc()).all()
    equipes = Equipe.query.filter_by(status="ativa").order_by(Equipe.nome.asc()).all()

    if request.method == "POST":
        farmacia_id = request.form.get("farmacia_id", type=int)
        equipe_id = request.form.get("equipe_id", type=int)
        data_resultado = str_para_data(request.form.get("data_resultado", "").strip())
        valor_realizado = request.form.get("valor_realizado", "0").strip()
        pedidos_realizados = request.form.get("pedidos_realizados", "0").strip()
        observacao = request.form.get("observacao", "").strip()

        if not farmacia_id:
            flash("Selecione a farmácia.", "danger")
            return render_template("resultados/editar.html", resultado=resultado, farmacias=farmacias, equipes=equipes)

        if not equipe_id:
            flash("Selecione a equipe.", "danger")
            return render_template("resultados/editar.html", resultado=resultado, farmacias=farmacias, equipes=equipes)

        equipe = Equipe.query.get(equipe_id)
        if not equipe:
            flash("Equipe inválida.", "danger")
            return render_template("resultados/editar.html", resultado=resultado, farmacias=farmacias, equipes=equipes)

        if equipe.farmacia_id != farmacia_id:
            flash("A equipe selecionada não pertence à farmácia escolhida.", "danger")
            return render_template("resultados/editar.html", resultado=resultado, farmacias=farmacias, equipes=equipes)

        if not data_resultado:
            flash("Informe a data do resultado.", "danger")
            return render_template("resultados/editar.html", resultado=resultado, farmacias=farmacias, equipes=equipes)

        try:
            valor_realizado_float = float(valor_realizado.replace(",", ".") or 0)
        except ValueError:
            flash("Informe um valor realizado válido.", "danger")
            return render_template("resultados/editar.html", resultado=resultado, farmacias=farmacias, equipes=equipes)

        try:
            pedidos_realizados_int = int(pedidos_realizados or 0)
        except ValueError:
            flash("Informe uma quantidade de pedidos válida.", "danger")
            return render_template("resultados/editar.html", resultado=resultado, farmacias=farmacias, equipes=equipes)

        resultado.farmacia_id = farmacia_id
        resultado.equipe_id = equipe_id
        resultado.data_resultado = data_resultado
        resultado.turno = equipe.turno
        resultado.valor_realizado = valor_realizado_float
        resultado.pedidos_realizados = pedidos_realizados_int
        resultado.observacao = observacao or None

        db.session.commit()

        flash("Resultado atualizado com sucesso.", "success")
        return redirect(url_for("resultados.listar"))

    return render_template("resultados/editar.html", resultado=resultado, farmacias=farmacias, equipes=equipes)