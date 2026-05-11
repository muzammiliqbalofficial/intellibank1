"""
Alert Service — Email (SendGrid), SMS (Twilio), WebSocket real-time
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, Set
from config.settings import settings

logger = logging.getLogger(__name__)

# WebSocket connected clients registry
_ws_clients: Set = set()


# ─────────────────────── Email ───────────────────────

def send_email_alert(subject: str, body: str, to_email: Optional[str] = None) -> bool:
    if not settings.SENDGRID_API_KEY:
        logger.warning("SendGrid API key not configured. Email not sent.")
        return False
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail

        message = Mail(
            from_email=settings.ALERT_EMAIL_FROM,
            to_emails=to_email or settings.ALERT_EMAIL_TO,
            subject=f"[IntelliBank Alert] {subject}",
            html_content=_build_email_html(subject, body),
        )
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        return response.status_code in (200, 202)
    except Exception as e:
        logger.error(f"Email alert failed: {e}")
        return False


def _build_email_html(subject: str, body: str) -> str:
    return f"""
    <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
    <div style="background:#1a237e;padding:20px;border-radius:8px 8px 0 0;">
      <h2 style="color:white;margin:0;">🏦 IntelliBank Alert</h2>
    </div>
    <div style="border:1px solid #ddd;padding:20px;border-radius:0 0 8px 8px;">
      <h3 style="color:#1a237e;">{subject}</h3>
      <p style="color:#333;">{body}</p>
      <hr/>
      <p style="color:#888;font-size:12px;">
        Generated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC |
        IntelliBank AI Analytics Platform
      </p>
    </div>
    </body></html>
    """


# ─────────────────────── SMS ───────────────────────

def send_sms_alert(message: str, to_number: Optional[str] = None) -> bool:
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        logger.warning("Twilio credentials not configured. SMS not sent.")
        return False
    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            body=f"[IntelliBank] {message}",
            from_=settings.TWILIO_FROM_NUMBER,
            to=to_number or settings.ALERT_SMS_TO,
        )
        return msg.sid is not None
    except Exception as e:
        logger.error(f"SMS alert failed: {e}")
        return False


# ─────────────────────── WebSocket ───────────────────────

def register_ws_client(websocket):
    _ws_clients.add(websocket)


def unregister_ws_client(websocket):
    _ws_clients.discard(websocket)


async def broadcast_alert(alert_data: dict):
    if not _ws_clients:
        return
    message = json.dumps(alert_data)
    disconnected = set()
    for ws in _ws_clients:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.add(ws)
    for ws in disconnected:
        _ws_clients.discard(ws)


# ─────────────────────── Unified Alert ───────────────────────

def send_fraud_alert(transaction_id: int, fraud_score: float,
                     amount: float, account_number: str,
                     top_features: list = None) -> dict:
    feature_text = ""
    if top_features:
        feature_text = "\nTop risk factors: " + ", ".join(
            [f["feature"] for f in top_features[:3]]
        )

    subject = f"High-Risk Fraud Detected — Score: {fraud_score:.0%}"
    body = (
        f"Transaction #{transaction_id} flagged as potential fraud.\n"
        f"Amount: PKR {amount:,.2f}\n"
        f"Account: {account_number}\n"
        f"Fraud Score: {fraud_score:.2%}{feature_text}"
    )

    email_sent = send_email_alert(subject, body)
    sms_sent = send_sms_alert(
        f"FRAUD ALERT: Txn #{transaction_id} | Score: {fraud_score:.0%} | PKR {amount:,.0f}"
    )

    alert_data = {
        "type": "fraud_alert",
        "transaction_id": transaction_id,
        "fraud_score": fraud_score,
        "amount": amount,
        "timestamp": datetime.utcnow().isoformat(),
        "channels": {"email": email_sent, "sms": sms_sent},
    }
    asyncio.create_task(broadcast_alert(alert_data)) if asyncio.get_event_loop().is_running() else None

    return {"email_sent": email_sent, "sms_sent": sms_sent, "alert_data": alert_data}


def send_churn_alert(customer_id: int, customer_name: str, churn_probability: float) -> dict:
    subject = f"High Churn Risk — {customer_name} ({churn_probability:.0%})"
    body = (
        f"Customer {customer_name} (ID: {customer_id}) has a high churn probability of "
        f"{churn_probability:.2%}. Immediate retention action recommended."
    )
    email_sent = send_email_alert(subject, body)
    sms_sent = send_sms_alert(
        f"CHURN RISK: {customer_name} | Probability: {churn_probability:.0%}"
    )
    return {"email_sent": email_sent, "sms_sent": sms_sent}
