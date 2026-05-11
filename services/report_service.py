"""
Report Service — PDF (ReportLab), Excel (XlsxWriter), CSV, JSON
"""
import io
import json
import csv
import os
from datetime import datetime
from typing import Optional
import pandas as pd
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Table, TableStyle,
                                 Spacer, HRFlowable, Image)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

BRAND_BLUE = colors.HexColor("#1a237e")
BRAND_GOLD = colors.HexColor("#f9a825")
LIGHT_BLUE = colors.HexColor("#e8eaf6")


def _get_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("BrandTitle", fontSize=22, textColor=BRAND_BLUE,
                               alignment=TA_CENTER, spaceAfter=6, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle("BrandSubtitle", fontSize=12, textColor=colors.grey,
                               alignment=TA_CENTER, spaceAfter=12))
    styles.add(ParagraphStyle("SectionHeader", fontSize=14, textColor=BRAND_BLUE,
                               spaceBefore=12, spaceAfter=6, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle("BodySmall", fontSize=9, textColor=colors.black))
    return styles


def _build_table(data: list, headers: list) -> Table:
    table_data = [headers] + data
    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BLUE]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def generate_pdf_report(title: str, sections: list, filename: str = None) -> bytes:
    """
    sections = [
        {"heading": "...", "paragraphs": ["..."], "table": {"headers": [...], "rows": [[...]]}},
    ]
    Returns PDF bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             rightMargin=2*cm, leftMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2*cm)
    styles = _get_styles()
    story = []

    # Header
    story.append(Paragraph("IntelliBank", styles["BrandTitle"]))
    story.append(Paragraph("AI-Powered Banking Data Analyst", styles["BrandSubtitle"]))
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND_GOLD))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(title, styles["SectionHeader"]))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}",
        styles["BodySmall"]
    ))
    story.append(Spacer(1, 0.5*cm))

    for section in sections:
        if section.get("heading"):
            story.append(Paragraph(section["heading"], styles["SectionHeader"]))
        for para in section.get("paragraphs", []):
            story.append(Paragraph(para, styles["BodySmall"]))
            story.append(Spacer(1, 0.2*cm))
        if section.get("table"):
            t = section["table"]
            story.append(_build_table(t["rows"], t["headers"]))
        story.append(Spacer(1, 0.4*cm))

    # Footer via page template
    doc.build(story)
    pdf_bytes = buffer.getvalue()

    if filename:
        path = os.path.join(REPORTS_DIR, filename)
        with open(path, "wb") as f:
            f.write(pdf_bytes)

    return pdf_bytes


def generate_excel_report(data: dict, filename: str = None) -> bytes:
    """data = {"Sheet1": df1, "Sheet2": df2}"""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        workbook = writer.book

        header_fmt = workbook.add_format({
            "bold": True, "bg_color": "#1a237e", "font_color": "white",
            "border": 1, "align": "center", "valign": "vcenter",
        })
        alt_row_fmt = workbook.add_format({"bg_color": "#e8eaf6"})
        title_fmt = workbook.add_format({
            "bold": True, "font_size": 14, "font_color": "#1a237e"
        })

        for sheet_name, df in data.items():
            df.to_excel(writer, sheet_name=sheet_name[:31], index=False, startrow=2)
            ws = writer.sheets[sheet_name[:31]]
            ws.write(0, 0, f"IntelliBank — {sheet_name}", title_fmt)

            for col_num, col_name in enumerate(df.columns):
                ws.write(2, col_num, col_name, header_fmt)
                ws.set_column(col_num, col_num, max(len(str(col_name)) + 4, 12))

    excel_bytes = buffer.getvalue()
    if filename:
        path = os.path.join(REPORTS_DIR, filename)
        with open(path, "wb") as f:
            f.write(excel_bytes)
    return excel_bytes


def dataframe_to_csv(df: pd.DataFrame) -> str:
    return df.to_csv(index=False)


def dataframe_to_json(df: pd.DataFrame) -> str:
    return df.to_json(orient="records", date_format="iso")


def generate_fraud_report(fraud_df: pd.DataFrame, summary: dict) -> bytes:
    sections = [
        {
            "heading": "Executive Summary",
            "paragraphs": [
                f"Total Transactions Analyzed: {summary.get('total', 0):,}",
                f"Fraudulent Transactions: {summary.get('fraud_count', 0):,} "
                f"({summary.get('fraud_rate', 0):.2%})",
                f"Total Amount at Risk: PKR {summary.get('total_amount_at_risk', 0):,.2f}",
                f"Alerts Resolved: {summary.get('resolved', 0):,}",
            ],
        },
        {
            "heading": "Fraud Transactions Detail",
            "table": {
                "headers": ["Transaction ID", "Amount (PKR)", "Fraud Score", "Risk Level", "Date"],
                "rows": fraud_df[fraud_df["is_fraud_predicted"] == 1][
                    ["transaction_ref", "amount", "fraud_probability", "risk_level", "transaction_date"]
                ].head(50).values.tolist() if not fraud_df.empty else [],
            },
        },
    ]
    return generate_pdf_report("Fraud Detection Report", sections,
                               f"fraud_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")


def generate_churn_report(churn_df: pd.DataFrame, summary: dict) -> bytes:
    sections = [
        {
            "heading": "Churn Analysis Summary",
            "paragraphs": [
                f"Total Customers Analyzed: {summary.get('total', 0):,}",
                f"High-Risk Customers: {summary.get('high_risk', 0):,}",
                f"Predicted Churn Rate: {summary.get('churn_rate', 0):.2%}",
                f"Estimated Revenue at Risk: PKR {summary.get('revenue_at_risk', 0):,.2f}",
            ],
        },
        {
            "heading": "High-Risk Customer List",
            "table": {
                "headers": ["Customer ID", "Name", "Churn Probability", "Risk Segment", "Branch"],
                "rows": churn_df[churn_df["will_churn"] == 1][
                    ["customer_number", "full_name", "churn_probability", "risk_segment", "branch"]
                ].head(50).values.tolist() if not churn_df.empty else [],
            },
        },
    ]
    return generate_pdf_report("Customer Churn Report", sections,
                               f"churn_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
