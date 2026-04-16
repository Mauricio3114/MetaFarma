from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.models import Farmacia, ResultadoVendedora, Vendedora

resultados_vendedoras_bp = Blueprint(
    "resultados_vendedoras",
    __name__,
    url_prefix="/resultados-vendedoras"
)


@resultados_vendedoras_bp.route("/novo", methods=["GET", "POST"])
@login_required
def novo():
    farmacias = Farmacia.query.order_by(Farmacia.nome.asc()).all()
    vendedoras = Vendedora.query.order_by(Vendedora.nome.asc()).all()

    if request.method == "POST":
        farmacia_id = request.form.get("farmacia_id", type=int)
        vendedora_id = request.form.get("vendedora_id", type=int)
        turno = request.form.get("turno", "").strip()
        valor = request.form.get("valor", "0").strip()
        pedidos = request.form.get("pedidos", "0").strip()

        if not farmacia_id:
            flash("Selecione a farmácia.", "danger")
            return render_template(
                "resultados_vendedoras/novo.html",
                farmacias=farmacias,
                vendedoras=vendedoras
            )

        if not vendedora_id:
            flash("Selecione a vendedora.", "danger")
            return render_template(
                "resultados_vendedoras/novo.html",
                farmacias=farmacias,
                vendedoras=vendedoras
            )

        if turno not in ["manha", "tarde"]:
            flash("Selecione um turno válido.", "danger")
            return render_template(
                "resultados_vendedoras/novo.html",
                farmacias=farmacias,
                vendedoras=vendedoras
            )

        try:
            valor_float = float(valor.replace(",", ".") or 0)
        except ValueError:
            flash("Informe um valor válido.", "danger")
            return render_template(
                "resultados_vendedoras/novo.html",
                farmacias=farmacias,
                vendedoras=vendedoras
            )

        try:
            pedidos_int = int(pedidos or 0)
        except ValueError:
            flash("Informe uma quantidade de pedidos válida.", "danger")
            return render_template(
                "resultados_vendedoras/novo.html",
                farmacias=farmacias,
                vendedoras=vendedoras
            )

        novo = ResultadoVendedora(
            farmacia_id=farmacia_id,
            vendedora_id=vendedora_id,
            turno=turno,
            valor_realizado=valor_float,
            pedidos=pedidos_int,
            data=date.today()
        )

        db.session.add(novo)
        db.session.commit()

        flash("Resultado da vendedora lançado com sucesso!", "success")
        return redirect(url_for("dashboard.index"))

    return render_template(
        "resultados_vendedoras/novo.html",
        farmacias=farmacias,
        vendedoras=vendedoras
    )