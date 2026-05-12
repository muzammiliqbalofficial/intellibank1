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


# ─────────────────────────────────────────────────────────────────────────────
# ANALYST — Technical Report
# ─────────────────────────────────────────────────────────────────────────────

def generate_analyst_pdf_report(df: pd.DataFrame, summary: dict) -> bytes:
    """Full technical report for Business Analyst — fraud + churn + dataset stats."""
    ts = datetime.now().strftime("%B %d, %Y at %H:%M")
    sections = []

    # ── Dataset Overview ──────────────────────────────────────────────────────
    overview_paras = [
        f"Report Generated: {ts}",
        f"Total Records: {summary.get('total_rows', len(df)):,}",
        f"Unique Customers: {summary.get('total_customers', 0):,}",
        f"Unique Branches: {summary.get('total_branches', 0):,}",
        f"Date Range: {summary.get('date_from', 'N/A')} to {summary.get('date_to', 'N/A')}",
        f"Total Transaction Volume: PKR {summary.get('total_revenue', 0):,.2f}",
        f"Average Transaction Amount: PKR {summary.get('avg_transaction', 0):,.2f}",
        f"Dataset Columns: {', '.join(df.columns.tolist())}",
    ]
    sections.append({"heading": "1. Dataset Overview", "paragraphs": overview_paras})

    # ── Fraud Analysis ────────────────────────────────────────────────────────
    if "is_fraud" in df.columns:
        fraud_count = int(df["is_fraud"].sum())
        fraud_rate  = df["is_fraud"].mean() * 100
        fraud_paras = [
            f"Total Fraudulent Transactions: {fraud_count:,}",
            f"Fraud Rate: {fraud_rate:.2f}%",
            f"Legitimate Transactions: {len(df) - fraud_count:,}",
        ]
        if "amount" in df.columns:
            fraud_amt = df[df["is_fraud"] == 1]["amount"].sum()
            fraud_paras.append(f"Total Amount at Risk: PKR {fraud_amt:,.2f}")
            fraud_paras.append(f"Average Fraud Amount: PKR {df[df['is_fraud']==1]['amount'].mean():,.2f}")

        sections.append({"heading": "2. Fraud Detection Analysis", "paragraphs": fraud_paras})

        # Fraud by category table
        if "merchant_category" in df.columns:
            cat_grp = (df.groupby("merchant_category")
                         .agg(total=("is_fraud","count"), fraudulent=("is_fraud","sum"))
                         .reset_index())
            cat_grp["fraud_rate_%"] = (cat_grp["fraudulent"] / cat_grp["total"] * 100).round(2)
            cat_grp = cat_grp.sort_values("fraudulent", ascending=False)
            sections.append({
                "heading": "2a. Fraud by Merchant Category",
                "paragraphs": [],
                "table": {
                    "headers": ["Category", "Total Txns", "Fraudulent", "Fraud Rate %"],
                    "rows": cat_grp.values.tolist(),
                },
            })

        # Fraud by transaction type
        if "transaction_type" in df.columns:
            type_grp = (df.groupby("transaction_type")
                          .agg(total=("is_fraud","count"), fraudulent=("is_fraud","sum"))
                          .reset_index())
            type_grp["fraud_rate_%"] = (type_grp["fraudulent"] / type_grp["total"] * 100).round(2)
            sections.append({
                "heading": "2b. Fraud by Transaction Type",
                "paragraphs": [],
                "table": {
                    "headers": ["Transaction Type", "Total", "Fraudulent", "Fraud Rate %"],
                    "rows": type_grp.values.tolist(),
                },
            })

    # ── Churn Analysis ────────────────────────────────────────────────────────
    if "is_churned" in df.columns:
        cust_df      = df.drop_duplicates("customer_id") if "customer_id" in df.columns else df
        churned      = int(cust_df["is_churned"].sum())
        churn_rate   = cust_df["is_churned"].mean() * 100
        churn_paras  = [
            f"Total Customers Analyzed: {len(cust_df):,}",
            f"Churned Customers: {churned:,}",
            f"Churn Rate: {churn_rate:.2f}%",
            f"Retained Customers: {len(cust_df) - churned:,}",
        ]
        if "credit_score" in cust_df.columns:
            avg_cs_churned  = cust_df[cust_df["is_churned"]==1]["credit_score"].mean()
            avg_cs_retained = cust_df[cust_df["is_churned"]==0]["credit_score"].mean()
            churn_paras.append(f"Avg Credit Score (Churned): {avg_cs_churned:.0f}")
            churn_paras.append(f"Avg Credit Score (Retained): {avg_cs_retained:.0f}")

        sections.append({"heading": "3. Customer Churn Analysis", "paragraphs": churn_paras})

        if "city" in cust_df.columns:
            city_churn = (cust_df.groupby("city")["is_churned"]
                                  .agg(["count","sum"])
                                  .reset_index())
            city_churn.columns = ["City", "Total Customers", "Churned"]
            city_churn["Churn Rate %"] = (city_churn["Churned"] / city_churn["Total Customers"] * 100).round(2)
            city_churn = city_churn.sort_values("Churn Rate %", ascending=False)
            sections.append({
                "heading": "3a. Churn by City",
                "paragraphs": [],
                "table": {
                    "headers": list(city_churn.columns),
                    "rows": city_churn.values.tolist(),
                },
            })

    # ── Branch Performance ────────────────────────────────────────────────────
    if "branch_code" in df.columns and "amount" in df.columns:
        br = df.groupby("branch_code").agg(
            Transactions=("amount","count"),
            Revenue=("amount","sum"),
        ).reset_index()
        if "is_fraud" in df.columns:
            br["Fraud Count"] = df.groupby("branch_code")["is_fraud"].sum().values
        br["Revenue"] = br["Revenue"].round(2)
        br = br.sort_values("Revenue", ascending=False)
        sections.append({
            "heading": "4. Branch Performance",
            "paragraphs": [],
            "table": {
                "headers": list(br.columns),
                "rows": br.values.tolist(),
            },
        })

    # ── Data Quality ──────────────────────────────────────────────────────────
    null_counts = df.isnull().sum()
    null_cols   = null_counts[null_counts > 0]
    if not null_cols.empty:
        quality_paras = [f"{col}: {cnt} missing values" for col, cnt in null_cols.items()]
        sections.append({"heading": "5. Data Quality Notes", "paragraphs": quality_paras})
    else:
        sections.append({"heading": "5. Data Quality Notes",
                         "paragraphs": ["No missing values detected in the dataset."]})

    return generate_pdf_report("Technical Analysis Report — Business Analyst", sections)


def generate_analyst_excel_report(df: pd.DataFrame, summary: dict) -> bytes:
    """Multi-sheet Excel technical report for Business Analyst."""
    sheets = {}

    # Summary sheet
    summary_rows = {k: [str(v)] for k, v in summary.items()}
    sheets["Summary"] = pd.DataFrame.from_dict(summary_rows, orient="index", columns=["Value"]).reset_index().rename(columns={"index":"Metric"})

    # Transactions sample
    sheets["Transactions"] = df.head(500)

    # Fraud breakdown
    if "is_fraud" in df.columns and "merchant_category" in df.columns:
        cat = (df.groupby("merchant_category")
                  .agg(Total=("is_fraud","count"), Fraudulent=("is_fraud","sum"))
                  .reset_index())
        cat["Fraud_Rate_%"] = (cat["Fraudulent"] / cat["Total"] * 100).round(2)
        sheets["Fraud by Category"] = cat

    # Churn breakdown
    if "is_churned" in df.columns and "city" in df.columns and "customer_id" in df.columns:
        cust_df = df.drop_duplicates("customer_id")
        city_c  = (cust_df.groupby("city")["is_churned"]
                           .agg(Total_Customers="count", Churned="sum")
                           .reset_index())
        city_c["Churn_Rate_%"] = (city_c["Churned"] / city_c["Total_Customers"] * 100).round(2)
        sheets["Churn by City"] = city_c

    # Branch performance
    if "branch_code" in df.columns and "amount" in df.columns:
        br = df.groupby("branch_code").agg(
            Transactions=("amount","count"),
            Total_Revenue=("amount","sum"),
        ).reset_index()
        if "is_fraud" in df.columns:
            br["Fraud_Count"] = df.groupby("branch_code")["is_fraud"].sum().values
        sheets["Branch Performance"] = br

    return generate_excel_report(sheets)


# ─────────────────────────────────────────────────────────────────────────────
# MANAGER — Executive Business Report
# ─────────────────────────────────────────────────────────────────────────────

def generate_manager_pdf_report(summary: dict, rev_df: pd.DataFrame, branch_df: pd.DataFrame) -> bytes:
    """Executive business report for Bank Manager — no technical ML details."""
    ts = datetime.now().strftime("%B %d, %Y at %H:%M")
    sections = []

    # ── Executive Summary ─────────────────────────────────────────────────────
    total_rev   = summary.get("total_revenue", 0)
    fraud_rate  = summary.get("fraud_rate", 0)
    churn_rate  = summary.get("churn_rate", 0)
    customers   = summary.get("total_customers", 0)

    exec_paras = [
        f"Report Generated: {ts}",
        f"Reporting Period: {summary.get('date_from','N/A')} to {summary.get('date_to','N/A')}",
        "",
        f"Total Revenue: PKR {total_rev:,.2f}",
        f"Total Customers: {customers:,}",
        f"Fraud Alert Rate: {fraud_rate:.2f}% {'[HIGH RISK]' if fraud_rate > 2 else '[Normal]'}",
        f"Customer Churn Rate: {churn_rate:.2f}% {'[HIGH RISK]' if churn_rate > 10 else '[Normal]'}",
        f"Total Transactions: {summary.get('total_rows', 0):,}",
        f"Top Performing Branch: {summary.get('top_branch', 'N/A')}",
    ]
    sections.append({"heading": "Executive Summary", "paragraphs": exec_paras})

    # ── Risk Assessment ───────────────────────────────────────────────────────
    risk_level_fraud  = "HIGH" if fraud_rate > 5 else "MEDIUM" if fraud_rate > 2 else "LOW"
    risk_level_churn  = "HIGH" if churn_rate > 20 else "MEDIUM" if churn_rate > 10 else "LOW"
    risk_paras = [
        f"Fraud Risk Level: {risk_level_fraud}",
        f"  - {summary.get('fraud_count', 0):,} fraudulent transactions detected",
        f"  - Action Required: {'Immediate investigation recommended.' if risk_level_fraud == 'HIGH' else 'Continue monitoring.' if risk_level_fraud == 'MEDIUM' else 'Risk within acceptable range.'}",
        "",
        f"Churn Risk Level: {risk_level_churn}",
        f"  - {summary.get('churned_count', 0):,} customers at high churn risk",
        f"  - Action Required: {'Launch immediate retention campaign.' if risk_level_churn == 'HIGH' else 'Review customer satisfaction metrics.' if risk_level_churn == 'MEDIUM' else 'Churn within acceptable range.'}",
    ]
    sections.append({"heading": "Risk Assessment", "paragraphs": risk_paras})

    # ── Revenue Performance ───────────────────────────────────────────────────
    if not rev_df.empty:
        rev_copy = rev_df.copy()
        rev_copy["date"] = pd.to_datetime(rev_copy["date"])
        rev_copy["month"] = rev_copy["date"].dt.to_period("M").astype(str)
        monthly = rev_copy.groupby("month")["revenue"].sum().tail(12).reset_index()
        monthly["revenue"] = monthly["revenue"].round(2)
        monthly.columns = ["Month", "Revenue (PKR)"]

        monthly_rows = monthly.values.tolist()
        if monthly_rows:
            total_m = sum(r[1] for r in monthly_rows)
            monthly_rows.append(["TOTAL", round(total_m, 2)])

        sections.append({
            "heading": "Revenue Performance (Last 12 Months)",
            "paragraphs": [],
            "table": {
                "headers": ["Month", "Revenue (PKR)"],
                "rows": monthly_rows,
            },
        })

    # ── Branch Performance ────────────────────────────────────────────────────
    if not branch_df.empty:
        br = branch_df.copy()
        display_cols = ["branch_code", "total_revenue", "transactions", "customers", "fraud_rate_pct"]
        display_cols = [c for c in display_cols if c in br.columns]
        br_display   = br[display_cols].copy()
        if "total_revenue" in br_display.columns:
            br_display["total_revenue"] = br_display["total_revenue"].apply(lambda x: f"PKR {x:,.0f}")
        if "fraud_rate_pct" in br_display.columns:
            br_display["fraud_rate_pct"] = br_display["fraud_rate_pct"].apply(lambda x: f"{x}%")

        header_map = {
            "branch_code":    "Branch",
            "total_revenue":  "Total Revenue",
            "transactions":   "Transactions",
            "customers":      "Customers",
            "fraud_rate_pct": "Fraud Rate",
        }
        br_display = br_display.rename(columns=header_map)

        sections.append({
            "heading": "Branch Performance Comparison",
            "paragraphs": [],
            "table": {
                "headers": list(br_display.columns),
                "rows": br_display.values.tolist(),
            },
        })

    # ── Strategic Recommendations ─────────────────────────────────────────────
    recommendations = []
    if fraud_rate > 2:
        recommendations.append("FRAUD: Strengthen transaction monitoring for high-risk merchant categories.")
    if churn_rate > 10:
        recommendations.append("CHURN: Initiate targeted retention programs for at-risk customer segments.")
    if not recommendations:
        recommendations.append("All KPIs are within acceptable thresholds. Maintain current strategies.")
    recommendations.append("Schedule quarterly review with Business Analyst team for detailed ML model insights.")

    sections.append({"heading": "Strategic Recommendations", "paragraphs": recommendations})

    return generate_pdf_report("Executive Business Report — Bank Manager", sections)


def generate_manager_excel_report(summary: dict, rev_df: pd.DataFrame, branch_df: pd.DataFrame) -> bytes:
    """Excel executive report for Bank Manager."""
    sheets = {}

    # KPI Summary
    kpi_data = {
        "Total Revenue (PKR)":    summary.get("total_revenue", 0),
        "Total Customers":        summary.get("total_customers", 0),
        "Total Transactions":     summary.get("total_rows", 0),
        "Fraud Rate (%)":         summary.get("fraud_rate", 0),
        "Fraudulent Transactions":summary.get("fraud_count", 0),
        "Churn Rate (%)":         summary.get("churn_rate", 0),
        "Churned Customers":      summary.get("churned_count", 0),
        "Top Branch":             summary.get("top_branch", "N/A"),
        "Reporting From":         summary.get("date_from", "N/A"),
        "Reporting To":           summary.get("date_to", "N/A"),
    }
    sheets["KPI Summary"] = pd.DataFrame(list(kpi_data.items()), columns=["Metric", "Value"])

    # Monthly revenue
    if not rev_df.empty:
        rc = rev_df.copy()
        rc["date"] = pd.to_datetime(rc["date"])
        rc["Month"] = rc["date"].dt.to_period("M").astype(str)
        monthly = rc.groupby("Month")["revenue"].sum().round(2).reset_index()
        monthly.columns = ["Month", "Revenue (PKR)"]
        sheets["Monthly Revenue"] = monthly

    # Branch performance
    if not branch_df.empty:
        sheets["Branch Performance"] = branch_df.copy()

    return generate_excel_report(sheets)
