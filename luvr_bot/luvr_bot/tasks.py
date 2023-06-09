from telegram_bot.notifications import send_shifts_start_soon_reminder, send_shifts_start_missing_reminder, \
    send_shifts_end_soon_reminder, send_shifts_end_missing_reminder
from .celery import app


@app.task
def notify_shift_start():
    send_shifts_start_soon_reminder()


@app.task
def notify_shift_start_absent():
    send_shifts_start_missing_reminder()


@app.task
def notify_shift_end():
    send_shifts_end_soon_reminder()

@app.task
def notify_shift_end_absent():
    send_shifts_end_missing_reminder()


app.conf.beat_schedule = {
    'notify_shift_start': {
        'task': 'luvr_bot.tasks.notify_shift_start',
        'schedule': 60.0,
        'args': ()
    },
    'notify_shift_start_absent': {
        'task': 'luvr_bot.tasks.notify_shift_start_absent',
        'schedule': 60.0,
        'args': ()
    },
    'daily_shift_end': {
        'task': 'luvr_bot.tasks.notify_shift_end',
        'schedule': 60.0,
        'args': ()
    },
    'notify_shift_end_absent': {
        'task': 'luvr_bot.tasks.notify_shift_end_absent',
        'schedule': 60.0,
        'args': ()
    },
}
