from io import BytesIO

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


VERT = colors.HexColor("#006b3f")
GRIS = colors.HexColor("#5c6770")
FOND = colors.HexColor("#e8f4ee")


def generer_pdf_rapport(stats, date_debut=None, date_fin=None, auteur=""):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm,
        title="Rapport de rapprochement ERA",
        author="BANGE Bank Cameroun",
    )
    styles = getSampleStyleSheet()
    titre = ParagraphStyle(
        "TitreBange",
        parent=styles["Heading1"],
        textColor=VERT,
        fontSize=16,
        spaceAfter=8,
    )
    sous = ParagraphStyle(
        "SousBange",
        parent=styles["Normal"],
        textColor=GRIS,
        fontSize=10,
        spaceAfter=14,
    )

    maintenant = timezone.now().strftime("%d/%m/%Y %H:%M")
    periode = "Période : toutes"
    if date_debut or date_fin:
        periode = f"Période : {date_debut or '…'} → {date_fin or '…'}"

    elements = [
        Paragraph("BANGE Bank Cameroun", titre),
        Paragraph("Rapport de rapprochement ERA — Direction OMT", styles["Heading2"]),
        Paragraph(
            f"Généré le {maintenant}"
            + (f" par {auteur}" if auteur else "")
            + f"<br/>{periode}",
            sous,
        ),
        Spacer(1, 8),
    ]

    indicateur = [
        ["Indicateur", "Valeur"],
        ["Transactions", str(stats["total_tx"])],
        ["Correspondances", str(stats["correspondances"])],
        ["Anomalies", str(stats["anomalies"])],
        ["Non rapprochées", str(stats["non_rapprochees"])],
    ]
    elements.append(_tableau(indicateur, [10 * cm, 6 * cm]))
    elements.append(Spacer(1, 16))
    elements.append(Paragraph("Répartition par partenaire", styles["Heading3"]))
    lignes_p = [["Partenaire", "Nombre"]]
    for ligne in stats["par_partenaire"]:
        lignes_p.append([ligne["source__nom"], str(ligne["total"])])
    if len(lignes_p) == 1:
        lignes_p.append(["Aucune donnée", "0"])
    elements.append(_tableau(lignes_p, [10 * cm, 6 * cm]))
    elements.append(Spacer(1, 16))
    elements.append(Paragraph("Répartition par type d'opération", styles["Heading3"]))
    lignes_t = [["Type d'opération", "Nombre"]]
    for ligne in stats["par_type"]:
        lignes_t.append([ligne["type_operation"], str(ligne["total"])])
    if len(lignes_t) == 1:
        lignes_t.append(["Aucune donnée", "0"])
    elements.append(_tableau(lignes_t, [10 * cm, 6 * cm]))

    doc.build(elements)
    return buffer.getvalue()


def _tableau(donnees, largeurs):
    table = Table(donnees, colWidths=largeurs)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), VERT),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BACKGROUND", (0, 1), (-1, -1), FOND),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d9e2dc")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return table
