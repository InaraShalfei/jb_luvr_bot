import datetime
import os

from . import constants
from .models import JobRequest
from django.db.models import Q
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()
token = os.getenv('TELEGRAM_TOKEN')
bot = Bot(token=token)


def send_shifts_start_soon_reminders():
    today = datetime.datetime.today()
    job_requests = JobRequest.objects.filter(Q(date_start__lte=today) & Q(date_end__gte=today) &
                                             (Q(last_notified_date__lt=today) | Q(last_notified_date__isnull=True)))
    for job_request in job_requests:
        shift_start = datetime.datetime.combine(job_request.date_start, job_request.shift_time_start)
        if (shift_start - datetime.datetime.now()).total_seconds() <= 30 * 60:
            for assignment in job_request.assignments.all():
                try:
                    shift_for_today = assignment.get_shift_for_date(today)
                    if assignment.employee.chat_id and (shift_for_today is None or shift_for_today.start_position is None):
                        time_start_str = datetime.datetime.strftime(shift_start, '%H:%M')
                        # TODO add keybutton
                        bot.send_message(chat_id=assignment.employee.chat_id,
                                         text=f'Ваша смена начнется в {time_start_str}.\nНе забудьте отметиться')
                except:
                    pass
        job_request.last_notified_date = today
        job_request.last_notification_status = constants.STATUS_30_MIN_REM_SHIFT_START
        job_request.save()


def send_shifts_start_15_min_ago():
    today = datetime.datetime.today()
    job_requests = JobRequest.objects.filter(Q(date_start__lte=today) & Q(date_end__gte=today) & Q(last_notification_status=constants.STATUS_30_MIN_REM_SHIFT_START))
    for job_request in job_requests:
        shift_start = datetime.datetime.combine(job_request.date_start, job_request.shift_time_start)
        if (datetime.datetime.now() - shift_start).total_seconds() >= 15 * 60:
            for assignment in job_request.assignments.all():
                try:
                    shift_for_today = assignment.get_shift_for_date(today)
                    if assignment.employee.chat_id and (shift_for_today is None or shift_for_today.start_position is None):

                        # TODO add keybutton

                        bot.send_message(chat_id=assignment.employee.chat_id,
                                         text=f'Ваша смена началась 15 минут назад.\nНеобходимо отправить геоданные о Приходе')
                except:
                    pass
        job_request.last_notified_date = today
        job_request.last_notification_status = constants.STATUS_15_MIN_SHIFT_START_ABS
        job_request.save()
