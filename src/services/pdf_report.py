from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    LongTable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.models import ValidationResult


STATUS_COLORS = {
    "PASS": colors.HexColor("#D1FAE5"),
    "WARNING": colors.HexColor("#FEF3C7"),
    "FAIL": colors.HexColor("#FEE2E2"),
}


def _text(value: Any) -> str:
    """Escape dynamic report text for ReportLab's Paragraph mini-markup."""
    if value is None or value == "":
        return "-"
    return escape(str(value)).replace("\n", "<br/>")


def _footer(canvas, document) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.drawString(15 * mm, 8 * mm, "Validator Deployment QA - Peninjauan engineer diperlukan")
    canvas.drawRightString(landscape(A4)[0] - 15 * mm, 8 * mm, f"Halaman {document.page}")
    canvas.restoreState()


def build_pdf_report(
    results: list[ValidationResult],
    summary: dict[str, int | str],
    filenames: dict[str, str | None],
) -> bytes:
    """Build a local PDF report in memory without embedding source documents."""
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=15 * mm,
        title="Laporan Validasi Deployment QA",
        author="Validator Deployment QA",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=18, leading=22, textColor=colors.HexColor("#0F172A"),
        alignment=TA_CENTER, spaceAfter=8,
    )
    small = ParagraphStyle(
        "Small", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=7.5, leading=9.5, textColor=colors.HexColor("#1E293B"),
    )
    small_bold = ParagraphStyle(
        "SmallBold", parent=small, fontName="Helvetica-Bold",
        textColor=colors.white, alignment=TA_CENTER,
    )
    body = ParagraphStyle(
        "ReportBody", parent=styles["BodyText"], fontSize=9, leading=12,
        textColor=colors.HexColor("#334155"),
    )

    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    story = [
        Paragraph("Laporan Validasi Deployment QA", title_style),
        Paragraph("Validasi selesai. Peninjauan engineer tetap diperlukan.", body),
        Spacer(1, 4 * mm),
    ]

    metadata = [
        [Paragraph("Dibuat (UTC)", small), Paragraph(_text(timestamp), small),
         Paragraph("Status Keseluruhan", small), Paragraph(f"<b>{_text(summary['overall_status'])}</b>", small)],
        [Paragraph("Dokumen QA", small), Paragraph(_text(filenames.get("qa")), small),
         Paragraph("Manifest", small), Paragraph(_text(filenames.get("manifest")), small)],
        [Paragraph("Hasil eksekusi", small), Paragraph(_text(filenames.get("run_results")), small),
         Paragraph("Skema YAML", small), Paragraph(_text(filenames.get("schema")), small)],
    ]
    metadata_table = Table(metadata, colWidths=[28 * mm, 86 * mm, 28 * mm, 112 * mm])
    metadata_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E2E8F0")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#E2E8F0")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.extend([metadata_table, Spacer(1, 4 * mm)])

    metrics = [[
        Paragraph(f"<b>Total</b><br/>{summary['total']}", body),
        Paragraph(f"<b>Lulus</b><br/>{summary['passed']}", body),
        Paragraph(f"<b>Peringatan</b><br/>{summary['warnings']}", body),
        Paragraph(f"<b>Gagal</b><br/>{summary['failed']}", body),
    ]]
    metrics_table = Table(metrics, colWidths=[63.5 * mm] * 4)
    metrics_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#E2E8F0")),
        ("BACKGROUND", (1, 0), (1, 0), STATUS_COLORS["PASS"]),
        ("BACKGROUND", (2, 0), (2, 0), STATUS_COLORS["WARNING"]),
        ("BACKGROUND", (3, 0), (3, 0), STATUS_COLORS["FAIL"]),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([metrics_table, Spacer(1, 5 * mm), Paragraph("Hasil Validasi", styles["Heading2"]), Spacer(1, 2 * mm)])

    headers = ["Kategori", "Objek", "Diharapkan", "Aktual", "Status", "Bukti / Penjelasan"]
    rows = [[Paragraph(header, small_bold) for header in headers]]
    status_rows: list[tuple[int, str]] = []
    for row_number, finding in enumerate(results, start=1):
        details = finding.evidence
        if finding.explanation:
            details = f"{details}\n{finding.explanation}"
        rows.append([
            Paragraph(_text(finding.category), small),
            Paragraph(_text(finding.object_name), small),
            Paragraph(_text(finding.expected), small),
            Paragraph(_text(finding.actual), small),
            Paragraph(f"<b>{_text(finding.status)}</b>", small),
            Paragraph(_text(details), small),
        ])
        status_rows.append((row_number, finding.status))

    results_table = LongTable(
        rows,
        repeatRows=1,
        colWidths=[25 * mm, 43 * mm, 32 * mm, 32 * mm, 19 * mm, 103 * mm],
    )
    table_commands = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    for row_number, status in status_rows:
        table_commands.append(("BACKGROUND", (4, row_number), (4, row_number), STATUS_COLORS[status]))
    results_table.setStyle(TableStyle(table_commands))
    story.extend([
        results_table,
        Spacer(1, 4 * mm),
        Paragraph(
            "Laporan ini dibuat oleh alat bantu pengambilan keputusan. Laporan ini tidak menyetujui, "
            "menolak, atau mengesahkan deployment produksi. Penilaian akhir tetap menjadi tanggung jawab engineer.",
            body,
        ),
    ])

    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()
