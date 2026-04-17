import os

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Faça login para acessar o sistema."
login_manager.login_message_category = "warning"


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object("config.Config")

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from app.models import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Usuario, int(user_id))

    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.farmacias import farmacias_bp
    from app.routes.metas import metas_bp
    from app.routes.equipes import equipes_bp
    from app.routes.badges import badges_bp
    from app.routes.vendedoras import vendedoras_bp
    from app.routes.escalas_vendedoras import escalas_vendedoras_bp
    from app.routes.configuracoes_dia import configuracoes_dia_bp
    from app.routes.calendario_mensal import calendario_mensal_bp
    from app.routes.feriados import feriados_bp
    from app.routes.relatorios import relatorios_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(farmacias_bp)
    app.register_blueprint(metas_bp)
    app.register_blueprint(equipes_bp)
    app.register_blueprint(badges_bp)
    app.register_blueprint(vendedoras_bp)
    app.register_blueprint(escalas_vendedoras_bp)
    app.register_blueprint(configuracoes_dia_bp)
    app.register_blueprint(calendario_mensal_bp)
    app.register_blueprint(feriados_bp)
    app.register_blueprint(relatorios_bp)

    with app.app_context():
        db.create_all()

    return app