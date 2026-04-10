from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.models import Usuario

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "").strip()

        usuario = Usuario.query.filter_by(email=email).first()

        if not usuario or not usuario.check_senha(senha):
            flash("E-mail ou senha inválidos.", "danger")
            return render_template("login.html")

        if not usuario.ativo:
            flash("Usuário inativo. Procure o administrador.", "warning")
            return render_template("login.html")

        login_user(usuario)
        flash("Login realizado com sucesso.", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu do sistema.", "info")
    return redirect(url_for("auth.login"))