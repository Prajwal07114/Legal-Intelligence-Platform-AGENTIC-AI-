"""
PDF report generation — app.utils.pdf_report

Renders the normalized export dict (see app.utils.report_export) into a
professional, branded PDF using reportlab. Print-safe palette derived
from the platform's dark "Legal Intelligence Command Room" theme
(gold accents, slate section bars) but on a white page background,
since dark-mode PDFs are unreadable/unprintable.

Sections (in order, per spec):
  1. Case Information       6. High-Risk Clauses
  2. Executive Summary      7. Recommendations
  3. Contract Analysis      8. Evidence Sources
  4. Compliance Findings    9. Agent Workflow Summary
  5. Risk Assessment       10. Disclaimer + Generated Timestamp
"""
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)

GOLD = colors.HexColor("#9C7A3B")
GOLD_DARK = colors.HexColor("#6B5A34")
SLATE = colors.HexColor("#1C2433")
SLATE_LIGHT = colors.HexColor("#EDEAE1")
INK = colors.HexColor("#1A1A1A")
MUTED = colors.HexColor("#5A5A5A")
CRITICAL = colors.HexColor("#8C2F39")
WARNING = colors.HexColor("#B5893D")
SUCCESS = colors.HexColor("#3E6B48")

PIPELINE_STAGES = [
    "Case Intake", "Legal Research", "Document Intelligence",
    "Compliance Review", "Red Flag Detection", "Risk Assessment", "Legal Report",
]

DISCLAIMER_TEXT = (
    "This report is AI-generated and is not a substitute for professional legal advice. "
    "Consult a licensed attorney before making decisions based on this analysis. "
    "Findings are observations grounded in the evidence cited and do not constitute "
    "legal conclusions or recommendations to act."
)


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("LICHeading1", parent=ss["Heading1"], textColor=GOLD_DARK,
                           fontSize=14, spaceBefore=14, spaceAfter=8, fontName="Helvetica-Bold"))
    ss.add(ParagraphStyle("LICBody", parent=ss["BodyText"], textColor=INK, fontSize=9.5, leading=14))
    ss.add(ParagraphStyle("LICMuted", parent=ss["BodyText"], textColor=MUTED, fontSize=8.5, leading=12))
    ss.add(ParagraphStyle("LICCaseTitle", parent=ss["Title"], textColor=SLATE, fontSize=20, spaceAfter=4))
    return ss


def _header_footer(canvas, doc, case_id: str):
    canvas.saveState()
    width, height = LETTER

    canvas.setFillColor(SLATE)
    canvas.rect(0, height - 0.55 * inch, width, 0.55 * inch, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(0.75 * inch, height - 0.37 * inch, "LEGAL INTELLIGENCE COMMAND ROOM")
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(width - 0.75 * inch, height - 0.37 * inch, f"CASE ID: {case_id}")

    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(0.75)
    canvas.line(0.75 * inch, 0.6 * inch, width - 0.75 * inch, 0.6 * inch)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(0.75 * inch, 0.42 * inch, "AI-generated \u2014 not a substitute for professional legal advice.")
    canvas.drawRightString(width - 0.75 * inch, 0.42 * inch, f"Page {doc.page}")
    canvas.restoreState()


def _findings_table(rows: list, col_widths: list) -> Table:
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SLATE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D8CDB8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SLATE_LIGHT]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def generate_pdf_report(data: dict) -> bytes:
    """data: the export dict from app.utils.report_export.build_export_data"""
    buf = io.BytesIO()
    styles = _styles()
    doc = SimpleDocTemplate(
        buf, pagesize=LETTER,
        topMargin=0.85 * inch, bottomMargin=0.85 * inch,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        title=f"Legal Intelligence Report - {data['case_id']}",
    )
    story = []

    story.append(Paragraph("LEGAL INTELLIGENCE REPORT", styles["LICCaseTitle"]))
    case_rows = [
        ["Case ID", data["case_id"]],
        ["Task Type", data.get("task_type", "\u2014")],
        ["Workflow Mode", (data.get("workflow_mode") or "single").upper()],
        ["Query", data.get("user_query", "\u2014")],
        ["Jurisdiction", data.get("jurisdiction") or "\u2014"],
        ["Governing Law", data.get("governing_law") or "\u2014"],
        ["Generated On", data.get("generated_on", "\u2014")],
    ]
    t = Table(case_rows, colWidths=[1.6 * inch, 4.9 * inch])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), GOLD_DARK),
        ("TEXTCOLOR", (1, 0), (1, -1), INK),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#D8CDB8")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    metrics = [
        ["Clauses Extracted", "High-Risk Clauses", "Compliance Score", "Risk Level"],
        [
            str(data.get("clauses_extracted", 0)),
            str(data.get("high_risk_clause_count", 0)),
            f"{data.get('compliance_score')}/100" if data.get("compliance_score") is not None else "\u2014",
            data.get("risk_level", "Low"),
        ],
    ]
    mt = Table(metrics, colWidths=[1.625 * inch] * 4)
    mt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SLATE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 7.5),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, 1), 13),
        ("TEXTCOLOR", (0, 1), (-1, 1), GOLD_DARK),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D8CDB8")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(mt)
    story.append(Spacer(1, 14))

    story.append(Paragraph("2. Executive Summary", styles["LICHeading1"]))
    high_count = data.get("high_risk_clause_count", 0)
    score = data.get("compliance_score")
    score_txt = f"{score}/100" if score is not None else "not computed"
    summary_txt = (
        f"This report presents the results of a {data.get('task_type', 'legal').lower()} analysis. "
        f"The overall risk level is <b>{data.get('risk_level', 'Low')}</b>, based on {high_count} "
        f"high-severity finding(s) and a compliance score of {score_txt}. "
    )
    if data.get("risk_level") in ("High", "Critical"):
        summary_txt += "Several findings in this report warrant prompt attention before this agreement is finalized or renewed."
    else:
        summary_txt += "No critical structural issues were identified, though the detailed findings below should still be reviewed."
    story.append(Paragraph(summary_txt, styles["LICBody"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("3. Contract Analysis", styles["LICHeading1"]))
    parties = data.get("parties") or []
    if parties:
        party_txt = ", ".join(
            (p.get("name", "") + (f" ({p['role']})" if p.get("role") else "")) if isinstance(p, dict) else str(p)
            for p in parties
        )
        story.append(Paragraph(f"<b>Parties:</b> {party_txt}", styles["LICBody"]))
   
    story.append(
    Paragraph(
        f"Effective date: {data.get('effective_date') or '—'}",
        styles["LICBody"]
    )
)

    clause_rows = [["Clause", "Status", "Summary"]]
    doc_intel = data.get("document_intelligence") or {}
    for key, label in [
        ("payment_terms", "Payment Terms"), ("confidentiality_clause", "Confidentiality"),
        ("liability_clause", "Liability"), ("indemnity_clause", "Indemnity"),
        ("termination_clause", "Termination"),
    ]:
        detail = doc_intel.get(key) or {}
        status = "On file" if detail.get("present") else "Not found"
        clause_rows.append([label, status, (detail.get("summary") or "\u2014")[:110]])
    story.append(Spacer(1, 6))
    story.append(_findings_table(clause_rows, [1.3 * inch, 0.9 * inch, 4.3 * inch]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("4. Compliance Findings", styles["LICHeading1"]))
    story.append(Paragraph(
        f"<b>Compliance score:</b> {data.get('compliance_score_value', 0)}/100", styles["LICBody"]))
    missing = data.get("missing_clauses") or []
    story.append(Paragraph(
        f"<b>Missing clauses:</b> {', '.join(missing) if missing else 'None'}", styles["LICBody"]))
    issues = data.get("compliance_issues") or []
    if issues:
        rows = [["Issue", "Severity", "Evidence"]]
        for i in issues:
            ev = "; ".join(e.get("label", "") for e in (i.get("evidence") or []))
            rows.append([i.get("issue", ""), i.get("severity", ""), ev or "\u2014"])
        story.append(Spacer(1, 6))
        story.append(_findings_table(rows, [2.6 * inch, 1.0 * inch, 2.9 * inch]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("5. Risk Assessment", styles["LICHeading1"]))
    story.append(Paragraph(f"<b>Overall risk level:</b> {data.get('risk_level', 'Low')}", styles["LICBody"]))
    risks = data.get("risks") or []
    if risks:
        for r in risks:
            story.append(Paragraph(f"\u2022 [{r.get('risk_level','')}] {r.get('reason','')}", styles["LICBody"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("6. High-Risk Clauses", styles["LICHeading1"]))
    high_flags = data.get("high_risk_flags") or []
    if high_flags:
        rows = [["Flag Type", "Severity", "Explanation"]]
        for f in high_flags:
            rows.append([f.get("flag_type", ""), f.get("severity", ""), (f.get("explanation", ""))[:140]])
        story.append(_findings_table(rows, [1.6 * inch, 0.9 * inch, 4.0 * inch]))
    else:
        story.append(Paragraph("No high-severity red flags detected.", styles["LICBody"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("7. Recommendations", styles["LICHeading1"]))
    recs = data.get("recommendations") or []
    if recs:
        for r in recs:
            story.append(Paragraph(f"\u2022 {r}", styles["LICBody"]))
    else:
        story.append(Paragraph("No specific review areas flagged.", styles["LICBody"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("8. Evidence Sources", styles["LICHeading1"]))
    evidence = data.get("evidence") or []
    if evidence:
        seen = set()
        rows = [["Evidence", "Source", "Excerpt"]]
        for e in evidence:
            key = (e.get("label"), e.get("source"))
            if key in seen:
                continue
            seen.add(key)
            rows.append([e.get("label", ""), e.get("source", ""), (e.get("quote") or "\u2014")[:90]])
        story.append(_findings_table(rows, [1.8 * inch, 1.5 * inch, 3.2 * inch]))
    else:
        story.append(Paragraph("No evidence references recorded.", styles["LICBody"]))
    story.append(Spacer(1, 10))

    sources = data.get("sources") or []
    if sources:
        story.append(Paragraph("Legal References Retrieved (RAG)", styles["LICBody"]))
        for s in sources[:10]:
            story.append(Paragraph(
                f"\u2022 [{s.get('source_type','')}] {s.get('source_name','')}", styles["LICMuted"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("9. Agent Workflow Summary", styles["LICHeading1"]))
    story.append(Paragraph(f"Workflow version: {data.get('agent_workflow_version','')}", styles["LICMuted"]))
    for i, stage in enumerate(PIPELINE_STAGES, start=1):
        story.append(Paragraph(f"\u2713 {i}. {stage} \u2014 complete", styles["LICBody"]))
    story.append(Spacer(1, 10))

    story.append(PageBreak())
    story.append(Paragraph("10. Disclaimer", styles["LICHeading1"]))
    story.append(Paragraph(DISCLAIMER_TEXT, styles["LICMuted"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"Generated by: {data.get('generated_by')}", styles["LICMuted"]))
    story.append(Paragraph(f"Generated on: {data.get('generated_on')}", styles["LICMuted"]))
    story.append(Paragraph(f"Report ID: {data.get('report_id')}", styles["LICMuted"]))

    doc.build(
        story,
        onFirstPage=lambda c, d: _header_footer(c, d, data["case_id"]),
        onLaterPages=lambda c, d: _header_footer(c, d, data["case_id"]),
    )
    return buf.getvalue()
