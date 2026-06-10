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

SYSTEM_PROMPT = """You are IntelliBank's SQL query generator. Convert natural language questions into PostgreSQL SELECT queries.

Database schema:
- customers(id INT, customer_number VARCHAR, full_name VARCHAR, credit_score INT,
            is_churned BOOLEAN, churn_probability FLOAT, branch_id INT)
- transactions(id INT, transaction_ref VARCHAR, account_id INT, amount FLOAT,
               transaction_type VARCHAR, merchant_category VARCHAR,
               is_fraud BOOLEAN, fraud_score FLOAT, transaction_date DATE)
- accounts(id INT, account_number VARCHAR, customer_id INT, branch_id INT,
           account_type VARCHAR, balance FLOAT, currency VARCHAR)
- fraud_alerts(id INT, transaction_id INT, fraud_score FLOAT, is_resolved BOOLEAN, created_at TIMESTAMP)
- prediction_logs(id INT, customer_id INT, model_type VARCHAR, prediction FLOAT,
                  confidence FLOAT, created_at TIMESTAMP)
- branches(id INT, name VARCHAR, code VARCHAR, city VARCHAR, region VARCHAR)
- users(id INT, username VARCHAR, email VARCHAR, role VARCHAR, branch_id INT, created_at TIMESTAMP)

Join paths:
  transactions → accounts: transactions.account_id = accounts.id
  accounts → customers:    accounts.customer_id = customers.id
  customers → branches:    customers.branch_id = branches.id

Critical rules:
1. Return ONLY a valid PostgreSQL SELECT query. NEVER use UPDATE, DELETE, DROP, INSERT, ALTER, or CREATE.
2. Always include LIMIT (max 1000).
3. Date column is transaction_date (type DATE). Use:
   - "today"       → transaction_date = CURRENT_DATE
   - "this month"  → transaction_date >= DATE_TRUNC('month', CURRENT_DATE)
   - "last 7 days" → transaction_date >= CURRENT_DATE - INTERVAL '7 days'
   - "last 30 days"→ transaction_date >= CURRENT_DATE - INTERVAL '30 days'
4. is_fraud and is_churned are BOOLEAN — use TRUE/FALSE, not 1/0.
5. For "customers churned this month": since customers.is_churned has no date, query
   prediction_logs WHERE model_type = 'churn' AND prediction >= 0.5 AND
   created_at >= DATE_TRUNC('month', CURRENT_DATE).
6. For revenue/amount queries use SUM(amount) on transactions.
7. Return the raw SQL only — no markdown, no code fences, no semicolons, no explanation."""

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

    import re
    dangerous_pattern = re.compile(
        r'\b(drop|delete|truncate|update|insert|alter|create\s+table|create\s+index)\b',
        re.IGNORECASE,
    )
    if dangerous_pattern.search(sql):
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
        elif not data:
            nl_answer = (
                "No records found for this query. This could mean: "
                "(1) the date range has no data in the database yet, "
                "(2) the filter condition did not match any rows, or "
                "(3) the relevant table is empty. "
                "Try broadening the time range or removing filters."
            )
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
