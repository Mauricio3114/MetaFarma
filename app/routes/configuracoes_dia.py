from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.models import BadgeMeta, ConfiguracaoDia, Farmacia

configuracoes_dia_bp = Blueprint("configuracoes_dia", __name__, url_prefix="/configuracoes-dia")

TIPOS_DIA = [
    "segunda",
    "terca",
    "quarta",
    "quinta",
    "sexta",
    "sabado",
    "domingo",
    "feriado",
]


@configuracoes_dia_bp.route("/")
@login_required
def listar():
    farmacia_id = request.args.get("farmacia_id", type=int)

    query = ConfiguracaoDia.query.join(Farmacia).join(BadgeMeta)
    if farmacia_id:
        query = query.filter(ConfiguracaoDia.farmacia_id == farmacia_id)

    configuracoes = query.order_by(ConfiguracaoDia.farmacia_id.asc(), ConfiguracaoDia.id.asc()).all()
    farmacias = Farmacia.query.order_by(Farmacia.nome.asc()).all()

    return render_template(
        "configuracoes_dia/listar.html",
        configuracoes=configuracoes,
        farmacias=farmacias,
        farmacia_id=farmacia_id,
        tipos_dia=TIPOS_DIA
    )


@configuracoes_dia_bp.route("/nova", methods=["GET", "POST"])
@login_required
def nova():
    farmacias = Farmacia.query.filter_by(status="ativa").order_by(Farmacia.nome.asc()).all()
    badges = BadgeMeta.query.filter_by(status="ativa").order_by(BadgeMeta.nome.asc()).all()

    if request.method == "POST":
        farmacia_id = request.form.get("farmacia_id", type=int)
        tipo_dia = request.form.get("tipo_dia", "").strip()
        badge_id = request.form.get("badge_id", type=int)
        observacao = request.form.get("observacao", "").strip()

        if not farmacia_id:
            flash("Selecione a farmácia.", "danger")
            return render_template("configuracoes_dia/nova.html", farmacias=farmacias, badges=badges, tipos_dia=TIPOS_DIA)

        if tipo_dia not in TIPOS_DIA:
            flash("Selecione um tipo de dia válido.", "danger")
            return render_template("configuracoes_dia/nova.html", farmacias=farmacias, badges=badges, tipos_dia=TIPOS_DIA)

        if not badge_id:
            flash("Selecione a badge.", "danger")
            return render_template("configuracoes_dia/nova.html", farmacias=farmacias, badges=badges, tipos_dia=TIPOS_DIA)

        existente = ConfiguracaoDia.query.filter_by(
            farmacia_id=farmacia_id,
            tipo_dia=tipo_dia
        ).first()

        if existente:
            flash("Já existe configuração para esse tipo de dia nessa farmácia.", "danger")
            return render_template("configuracoes_dia/nova.html", farmacias=farmacias, badges=badges, tipos_dia=TIPOS_DIA)

        nova_config = ConfiguracaoDia(
            farmacia_id=farmacia_id,
            tipo_dia=tipo_dia,
            badge_id=badge_id,
            observacao=observacao or None
        )

        db.session.add(nova_config)
        db.session.commit()

        flash("Configuração de dia cadastrada com sucesso.", "success")
        return redirect(url_for("configuracoes_dia.listar"))

    return render_template("configuracoes_dia/nova.html", farmacias=farmacias, badges=badges, tipos_dia=TIPOS_DIA)


@configuracoes_dia_bp.route("/editar/<int:config_id>", methods=["GET", "POST"])
@login_required
def editar(config_id):
    config = ConfiguracaoDia.query.get_or_404(config_id)
    farmacias = Farmacia.query.filter_by(status="ativa").order_by(Farmacia.nome.asc()).all()
    badges = BadgeMeta.query.filter_by(status="ativa").order_by(BadgeMeta.nome.asc()).all()

    if request.method == "POST":
        farmacia_id = request.form.get("farmacia_id", type=int)
        tipo_dia = request.form.get("tipo_dia", "").strip()
        badge_id = request.form.get("badge_id", type=int)
        observacao = request.form.get("observacao", "").strip()

        if not farmacia_id:
            flash("Selecione a farmácia.", "danger")
            return render_template("configuracoes_dia/editar.html", config=config, farmacias=farmacias, badges=badges, tipos_dia=TIPOS_DIA)

        if tipo_dia not in TIPOS_DIA:
            flash("Selecione um tipo de dia válido.", "danger")
            return render_template("configuracoes_dia/editar.html", config=config, farmacias=farmacias, badges=badges, tipos_dia=TIPOS_DIA)

        if not badge_id:
            flash("Selecione a badge.", "danger")
            return render_template("configuracoes_dia/editar.html", config=config, farmacias=farmacias, badges=badges, tipos_dia=TIPOS_DIA)

        existente = ConfiguracaoDia.query.filter(
            ConfiguracaoDia.farmacia_id == farmacia_id,
            ConfiguracaoDia.tipo_dia == tipo_dia,
            ConfiguracaoDia.id != config.id
        ).first()

        if existente:
            flash("Já existe outra configuração desse tipo de dia nessa farmácia.", "danger")
            return render_template("configuracoes_dia/editar.html", config=config, farmacias=farmacias, badges=badges, tipos_dia=TIPOS_DIA)

        config.farmacia_id = farmacia_id
        config.tipo_dia = tipo_dia
        config.badge_id = badge_id
        config.observacao = observacao or None

        db.session.commit()

        flash("Configuração atualizada com sucesso.", "success")
        return redirect(url_for("configuracoes_dia.listar"))

    return render_template("configuracoes_dia/editar.html", config=config, farmacias=farmacias, badges=badges, tipos_dia=TIPOS_DIA)