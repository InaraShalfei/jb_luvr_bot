from telegram_bot.notifications import send_shifts_start_soon_reminders
from .celery import app


@app.task
def notify():
    send_shifts_start_soon_reminders()


app.conf.beat_schedule = {
    'daily_notify': {
        'task': 'luvr_bot.tasks.notify',
        'schedule': 60.0,
        'args': ()
    },
}
