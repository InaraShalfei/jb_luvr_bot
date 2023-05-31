from telegram_bot.notifications import send_shifts_start_soon_reminders, send_shifts_start_15_min_ago
from .celery import app


@app.task
def notify_ahead():
    send_shifts_start_soon_reminders()


@app.task
def notify_15_min_ago():
    send_shifts_start_15_min_ago()


app.conf.beat_schedule = {
    'daily_ahead': {
        'task': 'luvr_bot.tasks.notify_ahead',
        'schedule': 60.0,
        'args': ()
    },
    'daily_15_min_after': {
        'task': 'luvr_bot.tasks.notify_15_min_ago',
        'schedule': 60.0,
        'args': ()
    },
}
