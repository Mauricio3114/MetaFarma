from datetime import date, datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.models import Farmacia, Meta

metas_bp = Blueprint("metas", __name__, url_prefix="/metas")


def str_para_data(valor):
    if not valor:
        return None
    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except ValueError:
        return None


def datas_padrao_por_tipo(tipo):
    hoje = date.today()

    if tipo in ["diaria", "turno1", "turno2"]:
        return hoje, hoje

    if tipo == "semanal":
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        fim_semana = inicio_semana + timedelta(days=6)
        return inicio_semana, fim_semana

    if tipo == "mensal":
        primeiro_dia = hoje.replace(day=1)

        if primeiro_dia.month == 12:
            proximo_mes = primeiro_dia.replace(year=primeiro_dia.year + 1, month=1, day=1)
        else:
            proximo_mes = primeiro_dia.replace(month=primeiro_dia.month + 1, day=1)

        ultimo_dia = proximo_mes - timedelta(days=1)
        return primeiro_dia, ultimo_dia

    return None, None


@metas_bp.route("/")
@login_required
def listar():
    farmacia_id = request.args.get("farmacia_id", type=int)
    tipo = request.args.get("tipo", "").strip()

    query = Meta.query.join(Farmacia)

    if farmacia_id:
        query = query.filter(Meta.farmacia_id == farmacia_id)

    if tipo:
        query = query.filter(Meta.tipo == tipo)

    metas = query.order_by(Meta.id.desc()).all()
    farmacias = Farmacia.query.order_by(Farmacia.nome.asc()).all()

    return render_template(
        "metas/listar.html",
        metas=metas,
        farmacias=farmacias,
        farmacia_id=farmacia_id,
        tipo=tipo
    )


@metas_bp.route("/nova", methods=["GET", "POST"])
@login_required
def nova():
    farmacias = Farmacia.query.order_by(Farmacia.nome.asc()).all()

    if not farmacias:
        flash("Cadastre pelo menos uma farmácia antes de criar metas.", "warning")
        return redirect(url_for("farmacias.nova"))

    if request.method == "POST":
        farmacia_id = request.form.get("farmacia_id", type=int)
        tipo = request.form.get("tipo", "").strip()
        valor_meta = request.form.get("valor_meta", "0").strip()
        pedidos_meta = request.form.get("pedidos_meta", "0").strip()
        data_inicio_str = request.form.get("data_inicio", "").strip()
        data_fim_str = request.form.get("data_fim", "").strip()
        observacao = request.form.get("observacao", "").strip()

        if not farmacia_id:
            flash("Selecione a farmácia.", "danger")
            return render_template("metas/nova.html", farmacias=farmacias)

        if tipo not in ["diaria", "semanal", "mensal", "turno1", "turno2"]:
            flash("Selecione um tipo de meta válido.", "danger")
            return render_template("metas/nova.html", farmacias=farmacias)

        try:
            valor_meta_float = float(valor_meta.replace(",", ".") or 0)
        except ValueError:
            flash("Informe um valor de meta válido.", "danger")
            return render_template("metas/nova.html", farmacias=farmacias)

        try:
            pedidos_meta_int = int(pedidos_meta or 0)
        except ValueError:
            flash("Informe uma quantidade de pedidos válida.", "danger")
            return render_template("metas/nova.html", farmacias=farmacias)

        data_inicio = str_para_data(data_inicio_str)
        data_fim = str_para_data(data_fim_str)

        if not data_inicio and not data_fim:
            data_inicio, data_fim = datas_padrao_por_tipo(tipo)

        meta = Meta(
            farmacia_id=farmacia_id,
            tipo=tipo,
            valor_meta=valor_meta_float,
            pedidos_meta=pedidos_meta_int,
            data_inicio=data_inicio,
            data_fim=data_fim,
            observacao=observacao or None
        )

        db.session.add(meta)
        db.session.commit()

        flash("Meta cadastrada com sucesso.", "success")
        return redirect(url_for("metas.listar"))

    return render_template("metas/nova.html", farmacias=farmacias)


@metas_bp.route("/editar/<int:meta_id>", methods=["GET", "POST"])
@login_required
def editar(meta_id):
    meta = Meta.query.get_or_404(meta_id)
    farmacias = Farmacia.query.order_by(Farmacia.nome.asc()).all()

    if request.method == "POST":
        farmacia_id = request.form.get("farmacia_id", type=int)
        tipo = request.form.get("tipo", "").strip()
        valor_meta = request.form.get("valor_meta", "0").strip()
        pedidos_meta = request.form.get("pedidos_meta", "0").strip()
        data_inicio_str = request.form.get("data_inicio", "").strip()
        data_fim_str = request.form.get("data_fim", "").strip()
        observacao = request.form.get("observacao", "").strip()

        if not farmacia_id:
            flash("Selecione a farmácia.", "danger")
            return render_template("metas/editar.html", meta=meta, farmacias=farmacias)

        if tipo not in ["diaria", "semanal", "mensal", "turno1", "turno2"]:
            flash("Selecione um tipo de meta válido.", "danger")
            return render_template("metas/editar.html", meta=meta, farmacias=farmacias)

        try:
            valor_meta_float = float(valor_meta.replace(",", ".") or 0)
        except ValueError:
            flash("Informe um valor de meta válido.", "danger")
            return render_template("metas/editar.html", meta=meta, farmacias=farmacias)

        try:
            pedidos_meta_int = int(pedidos_meta or 0)
        except ValueError:
            flash("Informe uma quantidade de pedidos válida.", "danger")
            return render_template("metas/editar.html", meta=meta, farmacias=farmacias)

        data_inicio = str_para_data(data_inicio_str)
        data_fim = str_para_data(data_fim_str)

        if not data_inicio and not data_fim:
            data_inicio, data_fim = datas_padrao_por_tipo(tipo)

        meta.farmacia_id = farmacia_id
        meta.tipo = tipo
        meta.valor_meta = valor_meta_float
        meta.pedidos_meta = pedidos_meta_int
        meta.data_inicio = data_inicio
        meta.data_fim = data_fim
        meta.observacao = observacao or None

        db.session.commit()

        flash("Meta atualizada com sucesso.", "success")
        return redirect(url_for("metas.listar"))

    return render_template("metas/editar.html", meta=meta, farmacias=farmacias)