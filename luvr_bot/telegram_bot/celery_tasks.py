import datetime
import os

from .models import JobRequest
from django.db.models import Q
from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import Updater

load_dotenv()
token = os.getenv('TELEGRAM_TOKEN')
bot = Bot(token=token)

updater = Updater(token)


def send_notification(update, context):
    today = datetime.datetime.today()
    job_requests = JobRequest.objects.filter(Q(date_start__lte=today) & Q(date_end__gte=today) &
                                             (Q(last_notified_date__lt=today) | Q(last_notified_date__isnull=True)))
    for job_request in job_requests:
        shift_start = datetime.datetime.combine(job_request.date_start, job_request.shift_time_start)
        if (shift_start - datetime.datetime.now()).total_seconds() <= 30 * 60:
            job_request.last_notified_date = today
            job_request.save()
            chat = update.effective_chat
            for assignment in job_request.assignments.all():
                if assignment.employee.chat_id:
                    time_start_str = datetime.datetime.strftime(shift_start, '%H:%M')
                    context.bot.send_message(chat_id=chat.id, text=f'Ваша смена начнется в {time_start_str}.\nНе забудьте отметиться')




