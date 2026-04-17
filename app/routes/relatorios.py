import calendar
from datetime import date
from io import BytesIO

from flask import Blueprint, make_response, render_template, request
from flask_login import login_required
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from sqlalchemy import extract

from app.models import (
    CalendarioVendedora,
    ConfiguracaoDia,
    EscalaVendedora,
    Farmacia,
    Feriado,
    Vendedora,
)

relatorios_bp = Blueprint("relatorios", __name__, url_prefix="/relatorios")

COR_PRIMARIA = colors.HexColor("#b91c1c")
COR_CAIXA = colors.HexColor("#f1f5f9")
COR_ZEBRA = colors.HexColor("#f8fafc")
COR_TEXTO = colors.black


def nome_dia_semana_pt(data_obj):
    dias = {
        0: "segunda",
        1: "terca",
        2: "quarta",
        3: "quinta",
        4: "sexta",
        5: "sabado",
        6: "domingo",
    }
    return dias.get(data_obj.weekday(), "")


def tipo_dia_da_data(data_obj, feriados_map):
    if data_obj in feriados_map:
        return "feriado"
    return nome_dia_semana_pt(data_obj)


def formatar_moeda(valor):
    return f'R$ {valor:,.2f}'.replace(",", "X").replace(".", ",").replace("X", ".")


def calcular_resumo_mensal_vendedoras(farmacia_id, mes, ano):
    escalas_fixas = EscalaVendedora.query.filter_by(
        farmacia_id=farmacia_id,
        status="ativa"
    ).all()

    calendarios_mes = CalendarioVendedora.query.filter(
        CalendarioVendedora.farmacia_id == farmacia_id,
        extract("month", CalendarioVendedora.data) == mes,
        extract("year", CalendarioVendedora.data) == ano
    ).all()

    feriados_mes = Feriado.query.filter(
        Feriado.farmacia_id == farmacia_id,
        extract("month", Feriado.data) == mes,
        extract("year", Feriado.data) == ano
    ).all()

    configuracoes = ConfiguracaoDia.query.filter_by(
        farmacia_id=farmacia_id
    ).all()

    mapa_feriados = {f.data: f for f in feriados_mes}
    mapa_config = {c.tipo_dia: c for c in configuracoes}
    mapa_turnos_fixos = {e.vendedora_id: e.turno for e in escalas_fixas}
    mapa_vendedoras = {e.vendedora_id: e.vendedora for e in escalas_fixas}
    mapa_calendario = {(c.vendedora_id, c.data): c for c in calendarios_mes}

    total_dias = calendar.monthrange(ano, mes)[1]
    acumulado_vendedoras = {}

    for dia in range(1, total_dias + 1):
        data_ref = date(ano, mes, dia)
        tipo_dia = tipo_dia_da_data(data_ref, mapa_feriados)
        config = mapa_config.get(tipo_dia)

        trabalhando = []
        for vendedora_id, turno_fixo in mapa_turnos_fixos.items():
            registro = mapa_calendario.get((vendedora_id, data_ref))
            if registro and registro.trabalha:
                turno_real = registro.turno_dia if registro.turno_dia in ["manha", "tarde"] else turno_fixo
                trabalhando.append({
                    "vendedora_id": vendedora_id,
                    "vendedora": mapa_vendedoras[vendedora_id],
                    "turno": turno_real
                })

        qtd_manha = sum(1 for item in trabalhando if item["turno"] == "manha")
        qtd_tarde = sum(1 for item in trabalhando if item["turno"] == "tarde")

        valor_manha = float(config.badge.valor_manha or 0) if config else 0
        valor_tarde = float(config.badge.valor_tarde or 0) if config else 0

        meta_individual_manha = (valor_manha / qtd_manha) if qtd_manha > 0 else 0
        meta_individual_tarde = (valor_tarde / qtd_tarde) if qtd_tarde > 0 else 0

        for item in trabalhando:
            meta_individual = meta_individual_manha if item["turno"] == "manha" else meta_individual_tarde
            vendedora_id = item["vendedora_id"]

            if vendedora_id not in acumulado_vendedoras:
                acumulado_vendedoras[vendedora_id] = {
                    "vendedora_id": vendedora_id,
                    "nome": item["vendedora"].nome,
                    "turno": item["turno"],
                    "dias_trabalhados": 0,
                    "meta_total": 0.0
                }

            acumulado_vendedoras[vendedora_id]["dias_trabalhados"] += 1
            acumulado_vendedoras[vendedora_id]["meta_total"] += meta_individual

    resumo = sorted(
        list(acumulado_vendedoras.values()),
        key=lambda x: x["meta_total"],
        reverse=True
    )

    total_dias_trabalhados = sum(item["dias_trabalhados"] for item in resumo)
    total_meta = sum(item["meta_total"] for item in resumo)

    return resumo, total_dias_trabalhados, total_meta


def calcular_escala_individual_vendedora(farmacia_id, vendedora_id, mes, ano):
    farmacia = Farmacia.query.get_or_404(farmacia_id)
    vendedora = Vendedora.query.get_or_404(vendedora_id)

    escala_fixa = EscalaVendedora.query.filter_by(
        farmacia_id=farmacia_id,
        vendedora_id=vendedora_id
    ).first()

    turno_base = escala_fixa.turno if escala_fixa else "-"

    escalas_fixas = EscalaVendedora.query.filter_by(
        farmacia_id=farmacia_id,
        status="ativa"
    ).all()

    calendarios_mes = CalendarioVendedora.query.filter(
        CalendarioVendedora.farmacia_id == farmacia_id,
        extract("month", CalendarioVendedora.data) == mes,
        extract("year", CalendarioVendedora.data) == ano
    ).all()

    feriados_mes = Feriado.query.filter(
        Feriado.farmacia_id == farmacia_id,
        extract("month", Feriado.data) == mes,
        extract("year", Feriado.data) == ano
    ).all()

    configuracoes = ConfiguracaoDia.query.filter_by(
        farmacia_id=farmacia_id
    ).all()

    mapa_feriados = {f.data: f for f in feriados_mes}
    mapa_config = {c.tipo_dia: c for c in configuracoes}
    mapa_turnos_fixos = {e.vendedora_id: e.turno for e in escalas_fixas}
    mapa_calendario = {(c.vendedora_id, c.data): c for c in calendarios_mes}

    total_dias_mes = calendar.monthrange(ano, mes)[1]
    detalhes = []
    dias_trabalhados = 0
    meta_total = 0.0

    for dia in range(1, total_dias_mes + 1):
        data_ref = date(ano, mes, dia)
        tipo_dia = tipo_dia_da_data(data_ref, mapa_feriados)
        config = mapa_config.get(tipo_dia)

        registro_vendedora = mapa_calendario.get((vendedora_id, data_ref))
        trabalha = bool(registro_vendedora and registro_vendedora.trabalha)

        turno_real = turno_base
        if registro_vendedora and registro_vendedora.turno_dia in ["manha", "tarde"]:
            turno_real = registro_vendedora.turno_dia

        qtd_mesmo_turno = 0
        if trabalha:
            for outra_id, turno_fixo in mapa_turnos_fixos.items():
                registro_outra = mapa_calendario.get((outra_id, data_ref))
                if registro_outra and registro_outra.trabalha:
                    turno_outra = registro_outra.turno_dia if registro_outra.turno_dia in ["manha", "tarde"] else turno_fixo
                    if turno_outra == turno_real:
                        qtd_mesmo_turno += 1

        valor_turno = 0.0
        meta_dia = 0.0
        if config:
            valor_turno = float(config.badge.valor_manha or 0) if turno_real == "manha" else float(config.badge.valor_tarde or 0)
            if trabalha and qtd_mesmo_turno > 0:
                meta_dia = valor_turno / qtd_mesmo_turno

        if trabalha:
            dias_trabalhados += 1
            meta_total += meta_dia

        detalhes.append({
            "data": data_ref,
            "tipo_dia": tipo_dia,
            "feriado_descricao": mapa_feriados.get(data_ref).descricao if data_ref in mapa_feriados else None,
            "badge_nome": config.badge.nome if config else "-",
            "trabalha": trabalha,
            "turno_real": turno_real,
            "qtd_mesmo_turno": qtd_mesmo_turno if trabalha else 0,
            "meta_dia": meta_dia
        })

    return {
        "farmacia": farmacia,
        "vendedora": vendedora,
        "turno_base": turno_base,
        "dias_trabalhados": dias_trabalhados,
        "meta_total": meta_total,
        "detalhes": detalhes
    }


def desenhar_topo_padrao(pdf, largura, altura, titulo):
    margem_esq = 2 * cm
    margem_dir = 2 * cm
    topo = altura - 2 * cm

    pdf.setFillColor(COR_PRIMARIA)
    pdf.roundRect(margem_esq, topo - 35, largura - margem_esq - margem_dir, 30, 8, fill=1, stroke=0)

    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(margem_esq + 12, topo - 23, "MetaFarma")

    pdf.setFillColor(COR_TEXTO)
    topo -= 60

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(margem_esq, topo, titulo)

    return topo, margem_esq, margem_dir


def caixa_resumo(pdf, largura, margem_esq, margem_dir, topo, texto_esq, texto_dir):
    pdf.setFillColor(COR_CAIXA)
    pdf.roundRect(margem_esq, topo - 42, largura - margem_esq - margem_dir, 36, 8, fill=1, stroke=0)
    pdf.setFillColor(COR_TEXTO)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(margem_esq + 14, topo - 20, texto_esq)
    pdf.drawRightString(largura - margem_dir - 14, topo - 20, texto_dir)


def desenhar_faixa_tabela(pdf, x, y, largura, altura=22):
    pdf.setFillColor(COR_PRIMARIA)
    pdf.roundRect(x, y - altura, largura, altura, 4, fill=1, stroke=0)
    pdf.setFillColor(colors.white)


# ===== PDF GERAL =====

def desenhar_cabecalho_tabela_resumo(pdf, largura, margem_esq, margem_dir, y):
    largura_util = largura - margem_esq - margem_dir
    desenhar_faixa_tabela(pdf, margem_esq, y, largura_util, 22)

    col_nome = margem_esq + 18
    col_turno = margem_esq + 320
    col_dias = margem_esq + 200
    col_meta = largura - margem_dir - 18

    pdf.setFont("Helvetica-Bold", 10)
    texto_y = y - 15
    pdf.drawString(col_nome, texto_y, "Vendedora")
    pdf.drawString(col_turno, texto_y, "Turno")
    pdf.drawString(col_dias, texto_y, "Dias")
    pdf.drawRightString(col_meta, texto_y, "Meta mensal")

def desenhar_linha_resumo(pdf, largura, margem_esq, margem_dir, y, item, zebra=False):
    largura_util = largura - margem_esq - margem_dir
    altura_linha = 22

    if zebra:
        pdf.setFillColor(COR_ZEBRA)
        pdf.rect(margem_esq, y - altura_linha + 2, largura_util, altura_linha, fill=1, stroke=0)

    col_nome = margem_esq + 18
    col_turno = margem_esq + 320
    col_dias = margem_esq + 210
    col_meta = largura - margem_dir - 18

    pdf.setFillColor(COR_TEXTO)
    pdf.setFont("Helvetica", 10)

    texto_y = y - 13
    pdf.drawString(col_nome, texto_y, item["nome"][:32])
    pdf.drawString(col_turno, texto_y, item["turno"])
    pdf.drawString(col_dias, texto_y, str(item["dias_trabalhados"]))
    pdf.drawRightString(col_meta, texto_y, formatar_moeda(item["meta_total"]))


# ===== PDF INDIVIDUAL =====

def desenhar_cabecalho_tabela_individual(pdf, largura, margem_esq, margem_dir, y):
    largura_util = largura - margem_esq - margem_dir
    desenhar_faixa_tabela(pdf, margem_esq, y, largura_util, 22)

    col_data = margem_esq + 14
    col_dia = margem_esq + 120
    col_situacao = margem_esq + 190
    col_turno = margem_esq + 360
    col_badge = margem_esq + 430
    col_meta = largura - margem_dir - 160

    pdf.setFont("Helvetica-Bold", 9)
    texto_y = y - 15
    pdf.drawString(col_data, texto_y, "Data")
    pdf.drawString(col_dia, texto_y, "Dia")
    pdf.drawString(col_situacao, texto_y, "Situação")
    pdf.drawString(col_turno, texto_y, "Turno")
    pdf.drawString(col_badge, texto_y, "Badge")
    pdf.drawRightString(col_meta, texto_y, "Meta do dia")


def desenhar_linha_individual(pdf, largura, margem_esq, margem_dir, y, item, zebra=False):
    largura_util = largura - margem_esq - margem_dir
    altura_linha = 20

    if zebra:
        pdf.setFillColor(COR_ZEBRA)
        pdf.rect(margem_esq, y - altura_linha + 2, largura_util, altura_linha, fill=1, stroke=0)

    col_data = margem_esq + 14
    col_dia = margem_esq + 120
    col_situacao = margem_esq + 190
    col_turno = margem_esq + 360
    col_badge = margem_esq + 430
    col_meta = largura - margem_dir - 160

    situacao = "Trabalha" if item["trabalha"] else "Folga"
    dia_label = f"{item['tipo_dia']}*" if item["feriado_descricao"] else item["tipo_dia"]

    pdf.setFillColor(COR_TEXTO)
    pdf.setFont("Helvetica", 9)

    texto_y = y - 12
    pdf.drawString(col_data, texto_y, item["data"].strftime("%d/%m/%Y"))
    pdf.drawString(col_dia, texto_y, dia_label[:12])
    pdf.drawString(col_situacao, texto_y, situacao)
    pdf.drawString(col_turno, texto_y, item["turno_real"])
    pdf.drawString(col_badge, texto_y, item["badge_nome"][:18])
    pdf.drawRightString(col_meta, texto_y, formatar_moeda(item["meta_dia"]))


@relatorios_bp.route("/")
@login_required
def index():
    hoje = date.today()
    mes = request.args.get("mes", type=int) or hoje.month
    ano = request.args.get("ano", type=int) or hoje.year
    farmacia_id = request.args.get("farmacia_id", type=int)

    farmacias = Farmacia.query.order_by(Farmacia.nome.asc()).all()
    vendedoras = []

    farmacia_atual = None
    resumo = []
    total_dias = 0
    total_meta = 0

    if farmacia_id:
        farmacia_atual = Farmacia.query.get(farmacia_id)
        vendedoras = (
            Vendedora.query
            .filter_by(farmacia_id=farmacia_id, status="ativa")
            .order_by(Vendedora.nome.asc())
            .all()
        )
        resumo, total_dias, total_meta = calcular_resumo_mensal_vendedoras(farmacia_id, mes, ano)

    return render_template(
        "relatorios/index.html",
        farmacias=farmacias,
        vendedoras=vendedoras,
        farmacia_id=farmacia_id,
        farmacia_atual=farmacia_atual,
        mes=mes,
        ano=ano,
        resumo=resumo,
        total_dias=total_dias,
        total_meta=total_meta
    )


@relatorios_bp.route("/pdf")
@login_required
def pdf_mensal():
    hoje = date.today()
    mes = request.args.get("mes", type=int) or hoje.month
    ano = request.args.get("ano", type=int) or hoje.year
    farmacia_id = request.args.get("farmacia_id", type=int)

    if not farmacia_id:
        return "Selecione a farmácia.", 400

    farmacia = Farmacia.query.get_or_404(farmacia_id)
    resumo, total_dias, total_meta = calcular_resumo_mensal_vendedoras(farmacia_id, mes, ano)

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4

    topo, margem_esq, margem_dir = desenhar_topo_padrao(
        pdf, largura, altura, "Relatório Mensal de Metas por Vendedora"
    )

    topo -= 22
    pdf.setFont("Helvetica", 11)
    pdf.drawString(margem_esq, topo, f"Farmácia: {farmacia.nome}")
    topo -= 16
    pdf.drawString(margem_esq, topo, f"Mês/Ano de referência: {mes:02d}/{ano}")
    topo -= 16
    pdf.drawString(margem_esq, topo, f"Emitido em: {hoje.strftime('%d/%m/%Y')}")

    topo -= 28

    caixa_resumo(
        pdf, largura, margem_esq, margem_dir, topo,
        f"Total de dias trabalhados: {total_dias}",
        f"Meta total do mês: {formatar_moeda(total_meta)}"
    )

    topo -= 58
    desenhar_cabecalho_tabela_resumo(pdf, largura, margem_esq, margem_dir, topo)
    topo -= 32

    if not resumo:
        pdf.setFillColor(COR_TEXTO)
        pdf.setFont("Helvetica", 11)
        pdf.drawString(margem_esq, topo, "Nenhum dado encontrado.")
    else:
        zebra = False
        for item in resumo:
            if topo < 90:
                pdf.showPage()
                topo, margem_esq, margem_dir = desenhar_topo_padrao(
                    pdf, largura, altura, "Relatório Mensal de Metas por Vendedora"
                )
                topo -= 24
                desenhar_cabecalho_tabela_resumo(pdf, largura, margem_esq, margem_dir, topo)
                topo -= 32

            desenhar_linha_resumo(pdf, largura, margem_esq, margem_dir, topo, item, zebra)
            topo -= 22
            zebra = not zebra

    topo -= 16
    if topo < 70:
        pdf.showPage()
        topo = altura - 3 * cm

    pdf.setFillColor(COR_CAIXA)
    pdf.roundRect(margem_esq, topo - 24, largura - margem_esq - margem_dir, 22, 6, fill=1, stroke=0)
    pdf.setFillColor(COR_TEXTO)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(margem_esq + 14, topo - 11, f"Total geral de dias: {total_dias}")
    pdf.drawRightString(largura - margem_dir - 14, topo - 11, f"Total geral das metas: {formatar_moeda(total_meta)}")

    pdf.save()
    buffer.seek(0)

    response = make_response(buffer.getvalue())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f'inline; filename=relatorio_metas_{farmacia.nome}_{mes:02d}_{ano}.pdf'
    return response


@relatorios_bp.route("/pdf-escala-vendedora")
@login_required
def pdf_escala_vendedora():
    hoje = date.today()
    mes = request.args.get("mes", type=int) or hoje.month
    ano = request.args.get("ano", type=int) or hoje.year
    farmacia_id = request.args.get("farmacia_id", type=int)
    vendedora_id = request.args.get("vendedora_id", type=int)

    if not farmacia_id:
        return "Selecione a farmácia.", 400
    if not vendedora_id:
        return "Selecione a vendedora.", 400

    dados = calcular_escala_individual_vendedora(farmacia_id, vendedora_id, mes, ano)

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4

    topo, margem_esq, margem_dir = desenhar_topo_padrao(
        pdf, largura, altura, "Escala Mensal da Vendedora"
    )

    topo -= 22
    pdf.setFont("Helvetica", 11)
    pdf.drawString(margem_esq, topo, f"Farmácia: {dados['farmacia'].nome}")
    topo -= 16
    pdf.drawString(margem_esq, topo, f"Vendedora: {dados['vendedora'].nome}")
    topo -= 16
    pdf.drawString(margem_esq, topo, f"Turno base: {dados['turno_base']}")
    topo -= 16
    pdf.drawString(margem_esq, topo, f"Mês/Ano de referência: {mes:02d}/{ano}")
    topo -= 16
    pdf.drawString(margem_esq, topo, f"Emitido em: {hoje.strftime('%d/%m/%Y')}")

    topo -= 28

    caixa_resumo(
        pdf, largura, margem_esq, margem_dir, topo,
        f"Dias trabalhados: {dados['dias_trabalhados']}",
        f"Meta mensal: {formatar_moeda(dados['meta_total'])}"
    )

    topo -= 58
    desenhar_cabecalho_tabela_individual(pdf, largura, margem_esq, margem_dir, topo)
    topo -= 32

    zebra = False
    for item in dados["detalhes"]:
        if topo < 80:
            pdf.showPage()
            topo, margem_esq, margem_dir = desenhar_topo_padrao(
                pdf, largura, altura, "Escala Mensal da Vendedora"
            )
            topo -= 24
            desenhar_cabecalho_tabela_individual(pdf, largura, margem_esq, margem_dir, topo)
            topo -= 32

        desenhar_linha_individual(pdf, largura, margem_esq, margem_dir, topo, item, zebra)
        topo -= 18
        zebra = not zebra

    topo -= 16
    if topo < 70:
        pdf.showPage()
        topo = altura - 3 * cm

    pdf.setFillColor(COR_CAIXA)
    pdf.roundRect(margem_esq, topo - 24, largura - margem_esq - margem_dir, 22, 6, fill=1, stroke=0)
    pdf.setFillColor(COR_TEXTO)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(margem_esq + 14, topo - 11, f"Quantidade de dias trabalhados: {dados['dias_trabalhados']}")
    pdf.drawRightString(largura - margem_dir - 14, topo - 11, f"Meta mensal da vendedora: {formatar_moeda(dados['meta_total'])}")

    pdf.save()
    buffer.seek(0)

    nome_arquivo = f"escala_{dados['vendedora'].nome}_{mes:02d}_{ano}.pdf".replace(" ", "_")
    response = make_response(buffer.getvalue())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f'inline; filename={nome_arquivo}'
    return response