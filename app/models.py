from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None


def agora_brasil():
    try:
        if ZoneInfo is not None:
            return datetime.now(ZoneInfo("America/Fortaleza"))
    except Exception:
        pass

    return datetime.now()


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=agora_brasil)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def __repr__(self):
        return f"<Usuario {self.email}>"


class Farmacia(db.Model):
    __tablename__ = "farmacias"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    responsavel = db.Column(db.String(150), nullable=True)
    cidade = db.Column(db.String(100), nullable=True)
    telefone = db.Column(db.String(30), nullable=True)
    status = db.Column(db.String(20), default="ativa")
    observacao = db.Column(db.String(255), nullable=True)
    criado_em = db.Column(db.DateTime, default=agora_brasil)

    metas = db.relationship("Meta", backref="farmacia", lazy=True, cascade="all, delete-orphan")
    equipes = db.relationship("Equipe", backref="farmacia", lazy=True, cascade="all, delete-orphan")
    resultados = db.relationship("Resultado", backref="farmacia", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Farmacia {self.nome}>"


class Meta(db.Model):
    __tablename__ = "metas"

    id = db.Column(db.Integer, primary_key=True)
    farmacia_id = db.Column(db.Integer, db.ForeignKey("farmacias.id"), nullable=False, index=True)

    tipo = db.Column(db.String(20), nullable=False, index=True)
    valor_meta = db.Column(db.Float, default=0)
    pedidos_meta = db.Column(db.Integer, default=0)

    data_inicio = db.Column(db.Date, nullable=True)
    data_fim = db.Column(db.Date, nullable=True)

    observacao = db.Column(db.String(255), nullable=True)
    criado_em = db.Column(db.DateTime, default=agora_brasil)

    def __repr__(self):
        return f"<Meta {self.tipo} - Farmacia {self.farmacia_id}>"


class Equipe(db.Model):
    __tablename__ = "equipes"

    id = db.Column(db.Integer, primary_key=True)
    farmacia_id = db.Column(db.Integer, db.ForeignKey("farmacias.id"), nullable=False, index=True)

    nome = db.Column(db.String(120), nullable=False)
    turno = db.Column(db.String(20), nullable=False, index=True)  # turno1 / turno2
    responsavel = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(20), default="ativa")
    observacao = db.Column(db.String(255), nullable=True)
    criado_em = db.Column(db.DateTime, default=agora_brasil)

    resultados = db.relationship("Resultado", backref="equipe", lazy=True)

    def __repr__(self):
        return f"<Equipe {self.nome} - {self.turno}>"


class Resultado(db.Model):
    __tablename__ = "resultados"

    id = db.Column(db.Integer, primary_key=True)

    farmacia_id = db.Column(db.Integer, db.ForeignKey("farmacias.id"), nullable=False, index=True)
    equipe_id = db.Column(db.Integer, db.ForeignKey("equipes.id"), nullable=False, index=True)

    data_resultado = db.Column(db.Date, nullable=False, index=True)
    turno = db.Column(db.String(20), nullable=False, index=True)

    valor_realizado = db.Column(db.Float, default=0)
    pedidos_realizados = db.Column(db.Integer, default=0)

    observacao = db.Column(db.String(255), nullable=True)
    criado_em = db.Column(db.DateTime, default=agora_brasil)

    def __repr__(self):
        return f"<Resultado {self.data_resultado} - {self.turno}>"