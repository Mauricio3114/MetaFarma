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
    vendedoras = db.relationship("Vendedora", backref="farmacia", lazy=True, cascade="all, delete-orphan")
    escalas_semanais = db.relationship("EscalaSemanal", backref="farmacia", lazy=True, cascade="all, delete-orphan")
    escalas_vendedoras = db.relationship("EscalaVendedora", backref="farmacia", lazy=True, cascade="all, delete-orphan")

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

    def __repr__(self):
        return f"<Vendedora {self.nome}>"


class EscalaSemanal(db.Model):
    __tablename__ = "escalas_semanais"

    id = db.Column(db.Integer, primary_key=True)
    farmacia_id = db.Column(db.Integer, db.ForeignKey("farmacias.id"), nullable=False, index=True)

    dia_semana = db.Column(db.String(20), nullable=False, index=True)
    badge_id = db.Column(db.Integer, db.ForeignKey("badges_meta.id"), nullable=False)

    quantidade_manha = db.Column(db.Integer, default=0)
    quantidade_tarde = db.Column(db.Integer, default=0)

    observacao = db.Column(db.String(255), nullable=True)
    criado_em = db.Column(db.DateTime, default=agora_brasil)

    badge = db.relationship("BadgeMeta", backref="escalas_semanais")

    def meta_individual_manha(self):
        valor = float(self.badge.valor_manha or 0) if self.badge else 0.0
        qtd = int(self.quantidade_manha or 0)
        if qtd <= 0:
            return 0.0
        return valor / qtd

    def meta_individual_tarde(self):
        valor = float(self.badge.valor_tarde or 0) if self.badge else 0.0
        qtd = int(self.quantidade_tarde or 0)
        if qtd <= 0:
            return 0.0
        return valor / qtd

    def __repr__(self):
        return f"<EscalaSemanal {self.dia_semana} - Farmacia {self.farmacia_id}>"


class EscalaVendedora(db.Model):
    __tablename__ = "escalas_vendedoras"

    id = db.Column(db.Integer, primary_key=True)
    farmacia_id = db.Column(db.Integer, db.ForeignKey("farmacias.id"), nullable=False, index=True)
    vendedora_id = db.Column(db.Integer, db.ForeignKey("vendedoras.id"), nullable=False, index=True)

    dia_semana = db.Column(db.String(20), nullable=False, index=True)
    turno = db.Column(db.String(20), nullable=False, index=True)  # manha / tarde

    observacao = db.Column(db.String(255), nullable=True)
    criado_em = db.Column(db.DateTime, default=agora_brasil)

    def __repr__(self):
        return f"<EscalaVendedora {self.dia_semana} - {self.turno}>"
    
class ResultadoVendedora(db.Model):
    __tablename__ = "resultados_vendedoras"

    id = db.Column(db.Integer, primary_key=True)

    farmacia_id = db.Column(db.Integer, db.ForeignKey("farmacias.id"), nullable=False)
    vendedora_id = db.Column(db.Integer, db.ForeignKey("vendedoras.id"), nullable=False)

    data = db.Column(db.Date, nullable=False)
    turno = db.Column(db.String(20), nullable=False)

    valor_realizado = db.Column(db.Float, default=0)
    pedidos = db.Column(db.Integer, default=0)

    criado_em = db.Column(db.DateTime, default=agora_brasil)

    farmacia = db.relationship("Farmacia")
    vendedora = db.relationship("Vendedora")

    def __repr__(self):
        return f"<ResultadoVendedora {self.vendedora_id} {self.data}>"