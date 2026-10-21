from apscheduler.schedulers.background import BackgroundScheduler

from app.services.daily_generation_sync_service import (
    run_daily_generation_sync,
)
from app.services.daily_performance_notification_service import (
    run_daily_performance_notification_check,
)

scheduler = BackgroundScheduler()


def start_scheduler() -> None:
    if scheduler.running:
        return

    scheduler.add_job(
        run_daily_generation_sync,
        trigger="cron",
        hour=2,
        minute=0,
        id="daily_generation_sync",
        replace_existing=True,
    )

    scheduler.add_job(
        run_daily_performance_notification_check,
        trigger="cron",
        hour=3,
        minute=0,
        id="daily_performance_notification_check",
        replace_existing=True,
    )

    scheduler.start()

    print("Scheduler iniciado. Sync diário agendado para 02:00.")


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown()
        print("Scheduler encerrado.")