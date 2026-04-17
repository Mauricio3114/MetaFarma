from datetime import datetime, date

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
    vendedoras = db.relationship("Vendedora", backref="farmacia", lazy=True, cascade="all, delete-orphan")
    configuracoes_dia = db.relationship("ConfiguracaoDia", backref="farmacia", lazy=True, cascade="all, delete-orphan")
    escalas_vendedoras = db.relationship("EscalaVendedora", backref="farmacia", lazy=True, cascade="all, delete-orphan")
    calendarios_vendedoras = db.relationship("CalendarioVendedora", backref="farmacia", lazy=True, cascade="all, delete-orphan")
    feriados = db.relationship("Feriado", backref="farmacia", lazy=True, cascade="all, delete-orphan")

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
    turno = db.Column(db.String(20), nullable=False, index=True)
    responsavel = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(20), default="ativa")
    observacao = db.Column(db.String(255), nullable=True)
    criado_em = db.Column(db.DateTime, default=agora_brasil)

    def __repr__(self):
        return f"<Equipe {self.nome} - {self.turno}>"


class Vendedora(db.Model):
    __tablename__ = "vendedoras"

    id = db.Column(db.Integer, primary_key=True)
    farmacia_id = db.Column(db.Integer, db.ForeignKey("farmacias.id"), nullable=False, index=True)
    nome = db.Column(db.String(120), nullable=False)
    telefone = db.Column(db.String(30), nullable=True)
    status = db.Column(db.String(20), default="ativa")
    observacao = db.Column(db.String(255), nullable=True)
    criado_em = db.Column(db.DateTime, default=agora_brasil)

    escalas = db.relationship("EscalaVendedora", backref="vendedora", lazy=True, cascade="all, delete-orphan")
    calendarios = db.relationship("CalendarioVendedora", backref="vendedora", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Vendedora {self.nome}>"


class BadgeMeta(db.Model):
    __tablename__ = "badges_meta"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True, index=True)
    cor_hex = db.Column(db.String(20), nullable=False)
    valor_manha = db.Column(db.Float, default=0)
    valor_tarde = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default="ativa")
    observacao = db.Column(db.String(255), nullable=True)
    criado_em = db.Column(db.DateTime, default=agora_brasil)

    def __repr__(self):
        return f"<BadgeMeta {self.nome}>"


class ConfiguracaoDia(db.Model):
    __tablename__ = "configuracoes_dia"

    id = db.Column(db.Integer, primary_key=True)
    farmacia_id = db.Column(db.Integer, db.ForeignKey("farmacias.id"), nullable=False, index=True)
    tipo_dia = db.Column(db.String(20), nullable=False, index=True)  # segunda...domingo, feriado
    badge_id = db.Column(db.Integer, db.ForeignKey("badges_meta.id"), nullable=False)
    observacao = db.Column(db.String(255), nullable=True)
    criado_em = db.Column(db.DateTime, default=agora_brasil)

    badge = db.relationship("BadgeMeta", backref="configuracoes_dia")

    def __repr__(self):
        return f"<ConfiguracaoDia {self.tipo_dia} - Farmacia {self.farmacia_id}>"


class EscalaVendedora(db.Model):
    __tablename__ = "escalas_vendedoras"

    id = db.Column(db.Integer, primary_key=True)
    farmacia_id = db.Column(db.Integer, db.ForeignKey("farmacias.id"), nullable=False, index=True)
    vendedora_id = db.Column(db.Integer, db.ForeignKey("vendedoras.id"), nullable=False, index=True)
    turno = db.Column(db.String(20), nullable=False, index=True)  # manha / tarde
    status = db.Column(db.String(20), default="ativa")
    observacao = db.Column(db.String(255), nullable=True)
    criado_em = db.Column(db.DateTime, default=agora_brasil)

    def __repr__(self):
        return f"<EscalaVendedora {self.vendedora.nome} - {self.turno}>"


class CalendarioVendedora(db.Model):
    __tablename__ = "calendarios_vendedoras"

    id = db.Column(db.Integer, primary_key=True)
    farmacia_id = db.Column(db.Integer, db.ForeignKey("farmacias.id"), nullable=False, index=True)
    vendedora_id = db.Column(db.Integer, db.ForeignKey("vendedoras.id"), nullable=False, index=True)
    data = db.Column(db.Date, nullable=False, index=True)
    trabalha = db.Column(db.Boolean, default=True)
    turno_dia = db.Column(db.String(20), default="fixo")  # fixo / manha / tarde
    observacao = db.Column(db.String(255), nullable=True)
    criado_em = db.Column(db.DateTime, default=agora_brasil)

    def __repr__(self):
        return f"<CalendarioVendedora {self.vendedora.nome} - {self.data}>"


class Feriado(db.Model):
    __tablename__ = "feriados"

    id = db.Column(db.Integer, primary_key=True)
    farmacia_id = db.Column(db.Integer, db.ForeignKey("farmacias.id"), nullable=False, index=True)
    data = db.Column(db.Date, nullable=False, index=True)
    descricao = db.Column(db.String(150), nullable=False)
    criado_em = db.Column(db.DateTime, default=agora_brasil)

    def __repr__(self):
        return f"<Feriado {self.data} - {self.descricao}>"