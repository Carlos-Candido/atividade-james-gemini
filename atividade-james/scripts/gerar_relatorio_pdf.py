"""Gera o PDF técnico a partir do Markdown (requer reportlab)."""

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

BASE = Path(__file__).resolve().parents[1]
FONTS = Path(r"C:\Windows\Fonts")
fonte_regular = FONTS / "arial.ttf"
fonte_negrito = FONTS / "arialbd.ttf"
if not (fonte_regular.is_file() and fonte_negrito.is_file()):
    fontes_linux = Path("/usr/share/fonts/liberation")
    fonte_regular = fontes_linux / "LiberationSans-Regular.ttf"
    fonte_negrito = fontes_linux / "LiberationSans-Bold.ttf"
pdfmetrics.registerFont(TTFont("Arial", str(fonte_regular)))
pdfmetrics.registerFont(TTFont("Arial-Bold", str(fonte_negrito)))
pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold")

normal = ParagraphStyle("Normal", fontName="Arial", fontSize=12, leading=18, spaceAfter=11, alignment=TA_LEFT)
titulo = ParagraphStyle("Titulo", parent=normal, fontName="Arial-Bold", fontSize=20, leading=27, spaceAfter=28, alignment=TA_CENTER, textColor=colors.HexColor("#7A3C12"))
secao = ParagraphStyle("Secao", parent=normal, fontName="Arial-Bold", fontSize=16, leading=23, spaceBefore=8, spaceAfter=18, textColor=colors.HexColor("#7A3C12"))
subsecao = ParagraphStyle("Subsecao", parent=normal, fontName="Arial-Bold", fontSize=12, leading=18, spaceBefore=10)


def formatar(texto: str) -> str:
    texto = html.escape(texto)
    texto = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", texto)
    texto = re.sub(r"\*(.+?)\*", r"<i>\1</i>", texto)
    texto = re.sub(r"`(.+?)`", r"<font name='Courier'>\1</font>", texto)
    return texto


def rodape(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D8D8D8"))
    canvas.line(55, 45, A4[0] - 55, 45)
    canvas.setFont("Arial", 9)
    canvas.drawString(55, 31, "Sistema de Análise de Sentimentos com LLM")
    canvas.drawRightString(A4[0] - 55, 31, f"Página {doc.page}")
    canvas.restoreState()


def gerar():
    origem = BASE / "RELATORIO_BACKEND.md"
    destino = BASE / "RELATORIO_BACKEND.pdf"
    texto = origem.read_text(encoding="utf-8")
    elementos = []
    bloco = []

    def descarregar():
        if bloco:
            conteudo = " ".join(linha.strip().rstrip("  ") for linha in bloco)
            elementos.append(Paragraph(formatar(conteudo), normal))
            bloco.clear()

    for linha in texto.splitlines():
        if linha == "<!-- pagebreak -->":
            descarregar()
            elementos.append(PageBreak())
        elif linha.startswith("# "):
            descarregar()
            elementos.append(Spacer(1, 85))
            elementos.append(Paragraph(formatar(linha[2:]), titulo))
        elif linha.startswith("## "):
            descarregar()
            elementos.append(Paragraph(formatar(linha[3:]), secao))
        elif linha.startswith("### "):
            descarregar()
            elementos.append(Paragraph(formatar(linha[4:]), subsecao))
        elif not linha.strip():
            descarregar()
        else:
            bloco.append(linha)
    descarregar()
    doc = SimpleDocTemplate(
        str(destino), pagesize=A4, leftMargin=62, rightMargin=62,
        topMargin=58, bottomMargin=64,
        title="Relatório Técnico - Sistema de Análise de Sentimentos",
        author="Projeto AV_FINAL",
    )
    doc.build(elementos, onFirstPage=rodape, onLaterPages=rodape)
    print(destino)


if __name__ == "__main__":
    gerar()
