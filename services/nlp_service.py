"""
NLP Query Service — LLM-powered SQL generation
Supports English and Urdu natural language queries
"""
import time
from langdetect import detect
from deep_translator import GoogleTranslator
from config.settings import settings

ANSWER_PROMPT = """You are IntelliBank's banking data analyst assistant.
The user asked a question and you have the database results.
Write a clear, concise conversational answer (2-4 sentences) summarising the key insights.
Use specific numbers from the data. Be direct and professional.
If results are empty, say so clearly.
Do NOT mention SQL or technical details. Respond in the same language as the user's question."""

SYSTEM_PROMPT = """You are IntelliBank's SQL query generator. Convert natural language questions about banking data into PostgreSQL queries.

Database schema:
- users(id, username, email, role, branch_id, created_at)
- branches(id, name, code, city, region)
- customers(id, customer_number, full_name, credit_score, is_churned, churn_probability, branch_id)
- accounts(id, account_number, customer_id, branch_id, account_type, balance, currency)
- transactions(id, transaction_ref, account_id, amount, transaction_type, merchant_category, is_fraud, fraud_score, transaction_date)
- fraud_alerts(id, transaction_id, fraud_score, is_resolved, created_at)
- prediction_logs(id, customer_id, model_type, prediction, confidence, created_at)

Rules:
1. Return ONLY valid PostgreSQL SELECT queries. Never UPDATE, DELETE, DROP, or INSERT.
2. Always use LIMIT clause (max 1000 rows).
3. Use proper JOINs for cross-table queries.
4. Return the SQL query only — no explanation, no markdown, no code blocks."""

URDU_BANKING_TERMS = {
    "لین دین": "transactions",
    "رقم": "amount",
    "کھاتہ": "account",
    "بینک": "bank",
    "شاخ": "branch",
    "گاہک": "customer",
    "دھوکہ": "fraud",
    "پیشن گوئی": "forecast",
    "رپورٹ": "report",
    "بیلنس": "balance",
}


def detect_language(text: str) -> str:
    try:
        lang = detect(text)
        return "ur" if lang in ("ur", "ar") else "en"
    except Exception:
        return "en"


def translate_to_english(text: str, source_lang: str = "ur") -> str:
    if source_lang == "en":
        return text
    try:
        for urdu_term, english_term in URDU_BANKING_TERMS.items():
            text = text.replace(urdu_term, english_term)
        return GoogleTranslator(source=source_lang, target="en").translate(text)
    except Exception:
        return text


def _generate_sql_groq(query: str) -> str:
    from groq import Groq
    client = Groq(api_key=settings.GROQ_API_KEY)
    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Generate SQL for: {query}"},
        ],
        temperature=0,
        max_tokens=500,
    )
    sql = response.choices[0].message.content.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql


def _generate_nl_answer(original_query: str, sql_data: list, detected_lang: str) -> str:
    import json
    from groq import Groq
    client = Groq(api_key=settings.GROQ_API_KEY)
    sample = sql_data[:20]
    data_str = json.dumps(sample, default=str)
    user_msg = (
        f"User question: {original_query}\n\n"
        f"Query results ({len(sql_data)} total rows, showing up to 20):\n{data_str}"
    )
    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": ANSWER_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        temperature=0.3,
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()


def generate_sql(query: str) -> dict:
    start = time.time()
    detected_lang = detect_language(query)
    translated_query = translate_to_english(query, detected_lang)

    sql = None
    success = False
    error = None

    if settings.GROQ_API_KEY:
        try:
            sql = _generate_sql_groq(translated_query)
            success = True
        except Exception as e:
            error = f"LLM API error: {e}"
    else:
        error = "No API key configured."

    elapsed_ms = (time.time() - start) * 1000

    return {
        "original_query":   query,
        "detected_language": detected_lang,
        "translated_query": translated_query,
        "generated_sql":    sql,
        "execution_time_ms": round(elapsed_ms, 2),
        "is_successful":    success,
        "error_message":    error,
    }


def execute_nlp_query(query: str, db_session) -> dict:
    result = generate_sql(query)
    if not result["is_successful"] or not result["generated_sql"]:
        return {**result, "query_result": [], "result_row_count": 0}

    sql = result["generated_sql"]

    dangerous = ["drop", "delete", "truncate", "update", "insert", "alter", "create"]
    if any(kw in sql.lower() for kw in dangerous):
        return {
            **result,
            "is_successful": False,
            "error_message": "Query contains disallowed operations.",
            "query_result": [],
            "result_row_count": 0,
        }

    nl_answer = None
    try:
        from sqlalchemy import text
        rows = db_session.execute(text(sql)).mappings().all()
        data = [dict(row) for row in rows]
        result["query_result"] = data
        result["result_row_count"] = len(data)

        if data and settings.GROQ_API_KEY:
            try:
                nl_answer = _generate_nl_answer(
                    query, data, result.get("detected_language", "en")
                )
            except Exception as e:
                result["nl_answer_error"] = str(e)
    except Exception as e:
        result["is_successful"] = False
        result["error_message"] = str(e)
        result["query_result"] = []
        result["result_row_count"] = 0

    result["nl_answer"] = nl_answer
    return result


def get_suggested_queries(language: str = "en") -> list:
    if language == "ur":
        return [
            "آج کے تمام لین دین دکھائیں",
            "کتنے گاہک اس ماہ چھوڑ گئے؟",
            "کراچی شاخ کا کل بیلنس کیا ہے؟",
            "گزشتہ ہفتے کے دھوکہ دہی کے واقعات دکھائیں",
            "سب سے زیادہ آمدنی والی شاخ کون سی ہے؟",
        ]
    return [
        "Show all transactions from today",
        "How many customers churned this month?",
        "What is the total balance for Karachi branch?",
        "Show fraud alerts from last week",
        "Which branch has the highest revenue?",
        "Top 10 customers by account balance",
        "Average transaction amount by merchant category",
        "Monthly fraud rate trend for last 6 months",
    ]
