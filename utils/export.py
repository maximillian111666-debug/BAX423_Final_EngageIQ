"""
Export utilities: generate downloadable engagement brief as CSV or PDF.
"""
import io
import csv
import json
from datetime import datetime


def export_csv(ranked_items: list[dict], summary: dict | None = None) -> bytes:
    output = io.StringIO()
    fieldnames = ["rank", "title", "source", "domain", "url", "stars",
                  "comments", "relevance", "community_health", "visibility",
                  "composite", "final_score"]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for item in ranked_items:
        row = {k: item.get(k, "") for k in fieldnames}
        writer.writerow(row)
    return output.getvalue().encode("utf-8")


def export_brief_pdf(ranked_items: list[dict], summary: dict,
                     profile_name: str = "User") -> bytes:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        Table, TableStyle, HRFlowable)
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                leftMargin=2*cm, rightMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("Title", parent=styles["Title"],
                                     fontSize=20, textColor=colors.HexColor("#1a1a2e"),
                                     alignment=TA_CENTER)
        h2 = ParagraphStyle("H2", parent=styles["Heading2"],
                             fontSize=13, textColor=colors.HexColor("#16213e"))
        normal = styles["Normal"]
        story = []

        story.append(Paragraph("EngageIQ Weekly Engagement Brief", title_style))
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(
            f"Profile: {profile_name} · Generated: {datetime.now().strftime('%B %d, %Y')}",
            ParagraphStyle("sub", parent=normal, alignment=TA_CENTER, textColor=colors.grey)
        ))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e94560")))
        story.append(Spacer(1, 0.4*cm))

        story.append(Paragraph("Top 10 Engagement Opportunities", h2))
        table_data = [["#", "Title", "Source", "Domain", "Score"]]
        for item in ranked_items[:10]:
            table_data.append([
                str(item.get("rank", "")),
                str(item.get("title", ""))[:55],
                item.get("source", ""),
                item.get("domain", "")[:20],
                f"{item.get('composite', 0):.0%}",
            ])
        t = Table(table_data, colWidths=[1*cm, 9*cm, 2.5*cm, 3.5*cm, 1.5*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5*cm))

        story.append(Paragraph("Dataset Summary", h2))
        total = summary.get("total_opportunities", 0)
        by_source = summary.get("by_source", [])
        src_str = " | ".join(f"{s['source']}: {s['count']}" for s in by_source)
        story.append(Paragraph(
            f"Total opportunities analyzed: {total:,}. Sources: {src_str}.", normal
        ))
        story.append(Spacer(1, 0.3*cm))

        top_domains = summary.get("by_domain", [])[:5]
        story.append(Paragraph("Top Domains by Volume", h2))
        dom_data = [["Domain", "Count", "Avg Stars"]] + [
            [d["domain"][:25], str(d["count"]), f"{d.get('avg_stars', 0):,.0f}"]
            for d in top_domains
        ]
        dt = Table(dom_data, colWidths=[8*cm, 3*cm, 3*cm])
        dt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f3460")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
        ]))
        story.append(dt)

        doc.build(story)
        return buf.getvalue()

    except ImportError:
        return _fallback_pdf_bytes(ranked_items, summary, profile_name)


def _fallback_pdf_bytes(ranked_items: list[dict], summary: dict, profile_name: str) -> bytes:
    lines = [
        f"EngageIQ Weekly Engagement Brief",
        f"Profile: {profile_name}",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "Top 10 Opportunities:",
    ]
    for item in ranked_items[:10]:
        lines.append(f"{item.get('rank', '?')}. {item.get('title', '')} "
                     f"[{item.get('source', '')}] Score={item.get('composite', 0):.0%}")
    return "\n".join(lines).encode("utf-8")
