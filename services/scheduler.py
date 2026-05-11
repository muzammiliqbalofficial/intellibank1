"""
Scheduled Reports — APScheduler
Automatically generates and emails weekly/monthly reports
"""
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from config.settings import settings

logger = logging.getLogger(__name__)
_scheduler = None


def _generate_and_send_weekly_report():
    logger.info("Generating scheduled weekly report...")
    try:
        from db.connection import SessionLocal
        from services.report_service import generate_pdf_report
        from services.alert_service import send_email_alert

        db = SessionLocal()
        # Collect summary stats
        from sqlalchemy import text, func
        from db.models import Transaction, Customer, FraudAlert

        total_txn = db.query(func.count(Transaction.id)).scalar() or 0
        fraud_count = db.query(func.count(FraudAlert.id)).filter_by(is_resolved=False).scalar() or 0
        churned = db.query(func.count(Customer.id)).filter_by(is_churned=True).scalar() or 0
        db.close()

        sections = [
            {
                "heading": "Weekly Summary",
                "paragraphs": [
                    f"Report Period: Week ending {datetime.now().strftime('%B %d, %Y')}",
                    f"Total Transactions: {total_txn:,}",
                    f"Unresolved Fraud Alerts: {fraud_count:,}",
                    f"Churned Customers (total): {churned:,}",
                ],
            }
        ]
        pdf_bytes = generate_pdf_report("Weekly Intelligence Report", sections)

        # Email with PDF
        recipients = settings.REPORT_RECIPIENTS.split(",")
        for recipient in recipients:
            send_email_alert(
                subject="Weekly Intelligence Report",
                body=f"Please find your weekly IntelliBank report for {datetime.now().strftime('%B %d, %Y')} attached.",
                to_email=recipient.strip(),
            )
        logger.info("Weekly report generated and sent.")
    except Exception as e:
        logger.error(f"Scheduled report failed: {e}")


def start_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        return _scheduler

    _scheduler = BackgroundScheduler(timezone="Asia/Karachi")

    # Weekly report — Monday 8 AM PKT
    _scheduler.add_job(
        _generate_and_send_weekly_report,
        trigger=CronTrigger(day_of_week="mon", hour=8, minute=0),
        id="weekly_report",
        name="Weekly Intelligence Report",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("IntelliBank scheduler started.")
    return _scheduler


def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")


def get_scheduled_jobs() -> list:
    global _scheduler
    if not _scheduler:
        return []
    return [
        {
            "id": job.id,
            "name": job.name,
            "next_run": str(job.next_run_time),
        }
        for job in _scheduler.get_jobs()
    ]


def trigger_report_now():
    """Manually trigger weekly report for testing."""
    _generate_and_send_weekly_report()
