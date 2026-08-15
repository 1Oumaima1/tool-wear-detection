"""
Phase 6 — Génération de rapports PDF.

Construit un rapport professionnel (ReportLab) à partir des vraies données
stockées (Predictions, Alerts, Machines, Tools) sur une période donnée,
avec des graphiques réels (Matplotlib, rendus en PNG puis intégrés au PDF).
Aucune donnée n'est inventée : si une section n'a rien à montrer, elle
l'indique explicitement plutôt que d'afficher un exemple.
"""
import logging
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # pas d'affichage interactif, on rend uniquement en PNG
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from sqlalchemy.orm import Session

from app.config import settings
from app.models.prediction import Prediction
from app.models.alert import Alert
from app.models.machine import Machine
from app.models.tool import Tool
from app.models.report import Report, ReportType

logger = logging.getLogger("reports_service")

REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

CLASS_COLORS = {"sharp": "#34D399", "used": "#F5A623", "dulled": "#F0453A"}

RECOMMENDATIONS_RULES = [
    (lambda ctx: ctx["dulled_ratio"] >= 0.3,
     "Taux élevé d'outils 'dulled' sur la période (>=30%). Revoir la fréquence de "
     "remplacement des outils et vérifier les paramètres de coupe."),
    (lambda ctx: ctx["open_alerts"] > 0,
     f"{{open_alerts}} alerte(s) encore non résolue(s) — planifier une intervention de maintenance."),
    (lambda ctx: ctx["avg_confidence"] < 0.6 and ctx["total_predictions"] > 0,
     "Confiance moyenne du modèle relativement basse sur la période — vérifier "
     "l'éclairage/l'angle de la caméra ou envisager un réentraînement."),
    (lambda ctx: ctx["total_predictions"] == 0,
     "Aucune inspection enregistrée sur cette période — vérifier que le pipeline "
     "vidéo (Phase 2) est bien exécuté régulièrement."),
]


def _period_bounds(report_type: ReportType, period_start=None, period_end=None):
    if period_start and period_end:
        return period_start, period_end
    end = datetime.utcnow()
    if report_type == ReportType.daily:
        start = end - timedelta(days=1)
    elif report_type == ReportType.weekly:
        start = end - timedelta(days=7)
    else:
        start = end - timedelta(days=30)
    return start, end


def _render_distribution_chart(predictions: list[Prediction]) -> str:
    counts = {"sharp": 0, "used": 0, "dulled": 0}
    for p in predictions:
        if p.predicted_class in counts:
            counts[p.predicted_class] += 1

    fig, ax = plt.subplots(figsize=(4, 3), dpi=140)
    labels = [k for k, v in counts.items() if v > 0]
    values = [v for v in counts.values() if v > 0]
    if values:
        ax.pie(
            values, labels=labels, autopct="%1.0f%%",
            colors=[CLASS_COLORS[l] for l in labels],
            textprops={"fontsize": 9},
        )
    else:
        ax.text(0.5, 0.5, "Aucune donnée", ha="center", va="center")
        ax.axis("off")
    ax.set_title("Répartition des prédictions", fontsize=10)

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    fig.savefig(tmp.name, bbox_inches="tight")
    plt.close(fig)
    return tmp.name


def _render_confidence_timeline(predictions: list[Prediction]) -> str:
    ordered = sorted(predictions, key=lambda p: p.created_at)
    fig, ax = plt.subplots(figsize=(6, 3), dpi=140)
    if ordered:
        xs = [p.created_at for p in ordered]
        ys = [p.confidence * 100 for p in ordered]
        colors_list = [CLASS_COLORS.get(p.predicted_class, "#9AA4B2") for p in ordered]
        ax.scatter(xs, ys, c=colors_list, s=14)
        ax.plot(xs, ys, color="#4C8DFF", alpha=0.4, linewidth=1)
        ax.set_ylabel("Confiance (%)", fontsize=9)
        ax.tick_params(axis="x", rotation=30, labelsize=7)
        ax.tick_params(axis="y", labelsize=8)
        ax.set_ylim(0, 100)
    else:
        ax.text(0.5, 0.5, "Aucune donnée", ha="center", va="center")
        ax.axis("off")
    ax.set_title("Évolution de la confiance sur la période", fontsize=10)
    fig.tight_layout()

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    fig.savefig(tmp.name, bbox_inches="tight")
    plt.close(fig)
    return tmp.name


def _build_recommendations(ctx: dict) -> list[str]:
    recs = []
    for condition, message in RECOMMENDATIONS_RULES:
        if condition(ctx):
            recs.append(message.format(**ctx))
    if not recs:
        recs.append("Aucune anomalie détectée sur la période — situation nominale.")
    return recs


def generate_report(
    db: Session,
    report_type: ReportType,
    period_start: datetime | None = None,
    period_end: datetime | None = None,
) -> Report:
    period_start, period_end = _period_bounds(report_type, period_start, period_end)

    predictions = (
        db.query(Prediction)
        .filter(Prediction.created_at >= period_start, Prediction.created_at <= period_end)
        .order_by(Prediction.created_at.asc())
        .all()
    )
    alerts = (
        db.query(Alert)
        .filter(Alert.created_at >= period_start, Alert.created_at <= period_end)
        .order_by(Alert.created_at.asc())
        .all()
    )
    machines = db.query(Machine).all()
    tools = db.query(Tool).all()
    machines_by_id = {m.id: m for m in machines}
    tools_by_id = {t.id: t for t in tools}

    total_predictions = len(predictions)
    dulled_count = sum(1 for p in predictions if p.predicted_class == "dulled")
    avg_confidence = (sum(p.confidence for p in predictions) / total_predictions) if total_predictions else 0
    open_alerts = sum(1 for a in alerts if not a.resolved)

    ctx = {
        "total_predictions": total_predictions,
        "dulled_ratio": (dulled_count / total_predictions) if total_predictions else 0,
        "avg_confidence": avg_confidence,
        "open_alerts": open_alerts,
    }
    recommendations = _build_recommendations(ctx)

    # --- Construction du PDF ---
    filename = f"report_{report_type.value}_{period_end.strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = REPORTS_DIR / filename

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleAgatronic", parent=styles["Title"], textColor=colors.HexColor("#12161C"))
    section_style = ParagraphStyle("Section", parent=styles["Heading2"], spaceBefore=14, spaceAfter=6)
    normal = styles["Normal"]

    doc = SimpleDocTemplate(str(file_path), pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    elements = []

    # Letterhead (texte stylé — pas de vrai fichier logo fourni avec le projet)
    elements.append(Paragraph("AGATRONIC", title_style))
    elements.append(Paragraph("Industrial AI Monitoring Platform — Rapport automatique", normal))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        f"Type de rapport : <b>{report_type.value.upper()}</b> &nbsp;|&nbsp; "
        f"Période : {period_start.strftime('%Y-%m-%d %H:%M')} → {period_end.strftime('%Y-%m-%d %H:%M')} "
        f"&nbsp;|&nbsp; Généré le {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC",
        normal,
    ))
    elements.append(Spacer(1, 12))

    # Résumé
    elements.append(Paragraph("Résumé", section_style))
    summary_table = Table(
        [
            ["Inspections totales", str(total_predictions)],
            ["Confiance moyenne", f"{avg_confidence*100:.1f}%"],
            ["Détections 'dulled'", f"{dulled_count} ({ctx['dulled_ratio']*100:.1f}%)"],
            ["Alertes déclenchées", str(len(alerts))],
            ["Alertes encore actives", str(open_alerts)],
            ["Machines suivies", str(len(machines))],
        ],
        colWidths=[8 * cm, 6 * cm],
    )
    summary_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F2F2F2")),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 12))

    # Graphiques
    elements.append(Paragraph("Graphiques", section_style))
    dist_chart_path = _render_distribution_chart(predictions)
    timeline_chart_path = _render_confidence_timeline(predictions)
    elements.append(RLImage(dist_chart_path, width=8 * cm, height=6 * cm))
    elements.append(Spacer(1, 6))
    elements.append(RLImage(timeline_chart_path, width=16 * cm, height=8 * cm))
    elements.append(Spacer(1, 12))

    # Machines & Tools
    elements.append(Paragraph("Machines & Outils", section_style))
    if not machines:
        elements.append(Paragraph("Aucune machine enregistrée.", normal))
    else:
        rows = [["Machine", "Localisation", "Statut", "Outil", "Dernier statut"]]
        for m in machines:
            machine_tools = [t for t in tools if t.machine_id == m.id]
            if not machine_tools:
                rows.append([m.name, m.location or "—", m.status.value, "—", "—"])
            for t in machine_tools:
                rows.append([m.name, m.location or "—", m.status.value, t.tool_identifier, t.last_status or "—"])
        table = Table(rows, colWidths=[3.5 * cm, 3.5 * cm, 2.5 * cm, 3.5 * cm, 3.5 * cm])
        table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#12161C")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ]))
        elements.append(table)
    elements.append(Spacer(1, 12))

    # Historique des prédictions (limité pour rester lisible ; le détail complet reste en base)
    elements.append(Paragraph("Historique des inspections (100 dernières de la période)", section_style))
    if not predictions:
        elements.append(Paragraph("Aucune inspection sur cette période.", normal))
    else:
        rows = [["Horodatage", "Machine", "Outil", "Prédiction", "Confiance"]]
        for p in predictions[-100:]:
            rows.append([
                p.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                machines_by_id.get(p.machine_id).name if machines_by_id.get(p.machine_id) else f"#{p.machine_id}",
                tools_by_id.get(p.tool_id).tool_identifier if tools_by_id.get(p.tool_id) else f"#{p.tool_id}",
                p.predicted_class.upper(),
                f"{p.confidence*100:.1f}%",
            ])
        table = Table(rows, colWidths=[4 * cm, 3.5 * cm, 3 * cm, 3 * cm, 2.5 * cm], repeatRows=1)
        table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#DDDDDD")),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#12161C")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ]))
        elements.append(table)
    elements.append(PageBreak())

    # Alertes
    elements.append(Paragraph("Alertes sur la période", section_style))
    if not alerts:
        elements.append(Paragraph("Aucune alerte déclenchée sur cette période.", normal))
    else:
        rows = [["Horodatage", "Machine", "Outil", "Sévérité", "Email envoyé", "Résolue"]]
        for a in alerts:
            rows.append([
                a.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                machines_by_id.get(a.machine_id).name if machines_by_id.get(a.machine_id) else f"#{a.machine_id}",
                tools_by_id.get(a.tool_id).tool_identifier if tools_by_id.get(a.tool_id) else f"#{a.tool_id}",
                a.severity.value,
                "Oui" if a.email_sent else "Non",
                "Oui" if a.resolved else "Non",
            ])
        table = Table(rows, colWidths=[4 * cm, 3 * cm, 3 * cm, 2.5 * cm, 2.5 * cm, 2 * cm], repeatRows=1)
        table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#DDDDDD")),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7A241F")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ]))
        elements.append(table)
    elements.append(Spacer(1, 12))

    # Recommandations
    elements.append(Paragraph("Recommandations de maintenance", section_style))
    for rec in recommendations:
        elements.append(Paragraph(f"• {rec}", normal))

    doc.build(elements)

    for tmp_path in (dist_chart_path, timeline_chart_path):
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass

    report = Report(
        report_type=report_type,
        period_start=period_start,
        period_end=period_end,
        file_path=str(file_path),
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    logger.info("Rapport %s généré : %s", report_type.value, file_path)
    return report
