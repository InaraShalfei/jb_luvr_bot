from telegram_bot.notifications import send_shifts_start_soon_reminders, send_shifts_start_15_min_ago, \
    send_shifts_end_reminder, send_shifts_end_15_min_ago
from .celery import app


@app.task
def notify_shift_start():
    send_shifts_start_soon_reminders()


@app.task
def notify_shift_start_15_min_ago():
    send_shifts_start_15_min_ago()


@app.task
def notify_shift_end():
    send_shifts_end_reminder()

@app.task
def notify_shift_end_15_min_after():
    send_shifts_end_15_min_ago()


app.conf.beat_schedule = {
    'daily_shift_start': {
        'task': 'luvr_bot.tasks.notify_shift_start',
        'schedule': 60.0,
        'args': ()
    },
    'daily_shift_start_15_min_after': {
        'task': 'luvr_bot.tasks.notify_shift_start_15_min_ago',
        'schedule': 60.0,
        'args': ()
    },

    'daily_shift_end': {
        'task': 'luvr_bot.tasks.notify_shift_end',
        'schedule': 60.0,
        'args': ()
    },
    'daily_shift_end_15_min_after': {
        'task': 'luvr_bot.tasks.notify_shift_end_15_min_after',
        'schedule': 60.0,
        'args': ()
    },
}
