import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
import streamlit as st
import pandas as pd

from app.utils.session import require_auth, get_db_session
from app.components.theme import load_css, apply_theme, render_page_header, render_footer
from app.components.sidebar import render_sidebar
from services.nlp_service import execute_nlp_query, get_suggested_queries

st.set_page_config(page_title="IntelliBank — NLP Query", page_icon="💬", layout="wide", initial_sidebar_state="expanded")
load_css()
user = require_auth()
apply_theme(st.session_state.get("theme", "light"))
render_sidebar()

lang = st.session_state.get("language", "en")
is_urdu = lang == "ur"

render_page_header(
    "اردو / English NLP Query" if is_urdu else "Natural Language Query",
    "بینکنگ ڈیٹا سے سوال پوچھیں" if is_urdu else "Ask questions about your banking data in plain English or Urdu",
    "💬"
)

# ── Query Interface ────────────────────────────────────────────────────────────
st.markdown("### Ask a Question")

col_main, col_sugg = st.columns([2, 1])

with col_main:
    placeholder_text = (
        "مثلاً: آج کے تمام لین دین دکھائیں" if is_urdu
        else "e.g., Show all transactions from today with fraud score > 0.8"
    )

    query = st.text_area(
        "Your Question",
        placeholder=placeholder_text,
        height=100,
        label_visibility="collapsed",
    )

    col_btn, col_lang = st.columns([3, 1])
    with col_btn:
        submit = st.button("Run Query", type="primary", use_container_width=True)
    with col_lang:
        st.info(f"Language: {'اردو (Urdu)' if is_urdu else 'English'}")

with col_sugg:
    st.markdown("**Suggested Queries:**")
    suggestions = get_suggested_queries(lang)
    for s in suggestions:
        if st.button(s, key=f"sugg_{s[:20]}", use_container_width=True):
            query = s
            submit = True

# ── Execute Query ──────────────────────────────────────────────────────────────
if submit and query:
    with st.spinner("Processing query..." if not is_urdu else "سوال پروسیس ہو رہا ہے..."):
        db = get_db_session()
        try:
            result = execute_nlp_query(query, db)

            # Log to DB
            from db.models import NLPQuery
            log = NLPQuery(
                user_id=user["id"],
                original_query=result["original_query"],
                detected_language=result.get("detected_language"),
                translated_query=result.get("translated_query"),
                generated_sql=result.get("generated_sql"),
                query_result=json.loads(json.dumps(result.get("query_result", []), default=str)),
                result_row_count=result.get("result_row_count", 0),
                execution_time_ms=result.get("execution_time_ms"),
                is_successful=result.get("is_successful", False),
                error_message=result.get("error_message"),
            )
            db.add(log)
            db.commit()
        finally:
            db.close()

    if result.get("detected_language") == "ur":
        st.info(f"Detected: Urdu | Translated to: {result.get('translated_query', '')}")

    # Show generated SQL
    with st.expander("Generated SQL", expanded=False):
        sql = result.get("generated_sql", "N/A")
        st.code(sql, language="sql")

    # Show execution info
    st.caption(
        f"Executed in {result.get('execution_time_ms', 0):.1f} ms | "
        f"{result.get('result_row_count', 0):,} rows returned"
    )

    # ── Natural language answer ────────────────────────────────────────────────
    nl_answer = result.get("nl_answer")
    if nl_answer:
        st.markdown(
            f"""<div style="background:#e8f4fd;border-left:4px solid #1a237e;
                padding:16px 20px;border-radius:8px;margin:12px 0;line-height:1.7;">
                🤖 <strong>IntelliBank AI:</strong><br><br>{nl_answer}
            </div>""",
            unsafe_allow_html=True,
        )
    elif result.get("nl_answer_error"):
        st.warning(f"AI answer failed: {result['nl_answer_error']}")

    # ── Results ────────────────────────────────────────────────────────────────
    if result.get("is_successful") and result.get("query_result"):
        df_result = pd.DataFrame(result["query_result"])
        st.markdown(f"### Results ({len(df_result):,} rows)")
        st.dataframe(df_result, use_container_width=True)

        # Export options
        exp_c1, exp_c2, exp_c3 = st.columns(3)
        with exp_c1:
            st.download_button("Download CSV", df_result.to_csv(index=False),
                               file_name="query_result.csv", mime="text/csv")
        with exp_c2:
            st.download_button("Download JSON", df_result.to_json(orient="records"),
                               file_name="query_result.json", mime="application/json")
        with exp_c3:
            if len(df_result) > 0 and len(df_result.columns) >= 2:
                import plotly.express as px
                num_cols = df_result.select_dtypes(include=["number"]).columns
                if len(num_cols) >= 1:
                    fig = px.bar(df_result.head(20), x=df_result.columns[0], y=num_cols[0],
                                 color_discrete_sequence=["#1a237e"])
                    st.plotly_chart(fig, use_container_width=True)

    elif not result.get("is_successful"):
        st.error(f"Query failed: {result.get('error_message', 'Unknown error')}")

elif submit and not query:
    st.warning("Please enter a question." if not is_urdu else "براہ کرم سوال درج کریں۔")

# ── Query History ──────────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("Query History", expanded=False):
    db = get_db_session()
    try:
        from db.models import NLPQuery
        history = (
            db.query(NLPQuery)
            .filter_by(user_id=user["id"])
            .order_by(NLPQuery.created_at.desc())
            .limit(10)
            .all()
        )
    finally:
        db.close()

    if history:
        for h in history:
            icon = "✅" if h.is_successful else "❌"
            st.markdown(f"{icon} `{h.original_query[:80]}` — {h.result_row_count or 0} rows — {str(h.created_at)[:16]}")
    else:
        st.info("No query history yet.")

render_footer()
