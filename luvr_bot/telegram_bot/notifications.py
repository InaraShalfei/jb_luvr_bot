import datetime
import os

import requests

from . import constants
from .jumisbar_api import JumisGo
from .models import JobRequest, Vacancy
from django.db.models import Q
from dotenv import load_dotenv
from telegram import Bot, KeyboardButton, ReplyKeyboardMarkup

load_dotenv()
token = os.getenv('TELEGRAM_TOKEN')
bot = Bot(token=token)
api = JumisGo('https://admin.jumisgo.kz')


def send_shifts_start_soon_reminder():
    today = datetime.datetime.today()
    job_requests = JobRequest.objects.filter(Q(date_start__lte=today) & Q(date_end__gte=today) &
                                             (Q(last_notified_date__lt=today) | Q(last_notified_date__isnull=True)))
    for job_request in job_requests:
        shift_start = datetime.datetime.combine(today, job_request.shift_time_start)
        if (shift_start - datetime.datetime.now()).total_seconds() <= 30 * 60:
            for assignment in job_request.assignments.all():
                try:
                    shift_for_today = assignment.get_shift_for_date(today)
                    if assignment.employee.chat_id and (shift_for_today is None or shift_for_today.start_position is None):
                        time_start_str = datetime.datetime.strftime(shift_start, '%H:%M')
                        location_button = KeyboardButton(text='Начать смену', request_location=True)
                        bot.send_message(chat_id=assignment.employee.chat_id,
                                         text=f'Ваша смена начнется в {time_start_str}.\nНе забудьте отметиться',
                                         reply_markup=ReplyKeyboardMarkup([[location_button]], one_time_keyboard=True,
                                                                          resize_keyboard=True
                                                                          ))
                except:
                    pass
            job_request.last_notified_date = today
            job_request.last_notification_status = constants.STATUS_SHIFT_STARTS_SOON
            job_request.save()


def send_shifts_start_missing_reminder():
    today = datetime.datetime.today()
    job_requests = JobRequest.objects.filter(Q(date_start__lte=today) & Q(date_end__gte=today) &
                                             Q(last_notification_status=constants.STATUS_SHIFT_STARTS_SOON) &
                                             Q(last_notified_date=today))
    for job_request in job_requests:
        shift_start = datetime.datetime.combine(today, job_request.shift_time_start)
        if (datetime.datetime.now() - shift_start).total_seconds() >= 5 * 60:
            for assignment in job_request.assignments.all():
                try:
                    shift_for_today = assignment.get_shift_for_date(today)
                    if assignment.employee.chat_id and (shift_for_today is None or shift_for_today.start_position is None):
                        location_button = KeyboardButton(text='Начать смену', request_location=True)
                        bot.send_message(chat_id=assignment.employee.chat_id,
                                         text=f'Ваша смена началась более 5 минут назад.\nНеобходимо отправить геоданные о Приходе',
                                         reply_markup=ReplyKeyboardMarkup([[location_button]], one_time_keyboard=True,
                                                                          resize_keyboard=True
                                                                          ))
                except:
                    pass
            job_request.last_notified_date = today
            job_request.last_notification_status = constants.STATUS_SHIFT_START_ABSENT
            job_request.save()


def send_shifts_end_soon_reminder():
    today = datetime.datetime.today()
    job_requests = JobRequest.objects.filter(Q(date_start__lte=today) & Q(date_end__gte=today) &
                                             Q(last_notification_status=constants.STATUS_SHIFT_START_ABSENT) &
                                             Q(last_notified_date=today))
    for job_request in job_requests:
        shift_end = datetime.datetime.combine(today, job_request.shift_time_end)
        if (datetime.datetime.now() - shift_end).total_seconds() >= 0:
            for assignment in job_request.assignments.all():
                try:
                    shift_for_today = assignment.get_shift_for_date(today)
                    if assignment.employee.chat_id and (
                            shift_for_today is None or shift_for_today.end_position is None):
                        time_end_str = datetime.datetime.strftime(shift_end, '%H:%M')
                        location_button = KeyboardButton(text='Закончить смену', request_location=True)
                        bot.send_message(chat_id=assignment.employee.chat_id,
                                         text=f'Ваша смена закончилась в {time_end_str}.\nНе забудьте отправить геоданные об Уходе',
                                         reply_markup=ReplyKeyboardMarkup([[location_button]], one_time_keyboard=True,
                                                                          resize_keyboard=True
                                                                          ))
                except:
                    pass
            job_request.last_notified_date = today
            job_request.last_notification_status = constants.STATUS_SHIFT_ENDS_SOON
            job_request.save()


def send_shifts_end_missing_reminder():
    today = datetime.datetime.today()
    job_requests = JobRequest.objects.filter(Q(date_start__lte=today) & Q(date_end__gte=today) &
                                             Q(last_notification_status=constants.STATUS_SHIFT_ENDS_SOON) &
                                             Q(last_notified_date=today))
    for job_request in job_requests:
        shift_end = datetime.datetime.combine(today, job_request.shift_time_end)
        if (datetime.datetime.now() - shift_end).total_seconds() >= 5 * 60:
            for assignment in job_request.assignments.all():
                try:
                    shift_for_today = assignment.get_shift_for_date(today)
                    if assignment.employee.chat_id and (
                            shift_for_today is None or shift_for_today.end_position is None):
                        location_button = KeyboardButton(text='Закончить смену', request_location=True)
                        bot.send_message(chat_id=assignment.employee.chat_id,
                                         text=f'Ваша смена закончилась более 5 минут назад.\nНеобходимо отправить геоданные об Уходе',
                                         reply_markup=ReplyKeyboardMarkup([[location_button]], one_time_keyboard=True,
                                                                          resize_keyboard=True
                                                                          ))
                except:
                    pass
            job_request.last_notified_date = today
            job_request.last_notification_status = constants.STATUS_SHIFT_END_ABSENT
            job_request.save()


def notify_about_vacancies():
    # channels = {
    #     'Продавец': 'https://t.me/+crT4-riWQFI1MjYy',
    #     'Грузчик': 'https://t.me/+7oIiSSoBxU81NmY6',
    #     'Кассир': 'https://t.me/+Z-Bx_3ESYjhmYzYy',
    #     'Кондитер': 'https://t.me/+D3PWC-k5-hBhNjYy',
    #     'Повар': 'https://t.me/+Rn5pr75Xf3NlMDU6',
    #     'Пекарь': 'https://t.me/+sg4QDVzwVhRjMmIy',
    #     'Мясник': 'https://t.me/+w2p_bMRZxyUxOWMy',
    #     'Тележечник': 'https://t.me/+iqoes7ZCSgE4NGMy',
    #     'Кухонный работник': 'https://t.me/+sp4KDwa099hkYWI6',
    # }
    groups = {
        'Продавец': '@prodavets_jumisbar',
        # 'Пекарь': '-967759736'
    }
    vacancies = api.get_vacancies()
    for vacancy in vacancies:
        vacancy_id = vacancy['id']
        if Vacancy.objects.filter(vacancy_id=vacancy_id).exists():
            continue
        else:
            branch = vacancy['branch_description'] if vacancy['branch_description'] else ''
            address = vacancy['branch_address'] if vacancy['branch_address'] else ''
            position = vacancy['title'] if vacancy['title'] else ''
            print(position)
            rate = vacancy['rate_hour'] if vacancy['rate_hour'] else ''
            Vacancy.objects.create(vacancy_id=vacancy_id, vacancy_name=position)
            address = f'{branch} - {address}\n📌{position}\n'
            salary = f'✅Оплата: {rate} тнг/час\nhttp://t.me/jb_luvr_bot?start=vacancy{vacancy_id}'

            shifts = {}
            schedule = vacancy['schedules']
            for shift in schedule:
                shift_start = shift['start_at']
                shift_end = shift['finish_at']
                key = f'{shift_start} - {shift_end}'
                if key not in shifts:
                    shifts[key] = []
                shifts[key].append(shift['date'])
            for shift_time, dates in shifts.items():
                sorted_dates = sorted(dates)
                shift_start_date = datetime.datetime.strptime(sorted_dates[0], '%Y-%m-%d')
                shift_start_date = datetime.datetime.strftime(shift_start_date, '%d.%m.%Y')
                shift_end_date = datetime.datetime.strptime(sorted_dates[-1], '%Y-%m-%d')
                shift_end_date = datetime.datetime.strftime(shift_end_date, '%d.%m.%Y')
                if position in groups:
                    bot.send_message(chat_id=groups[position],
                                     text=f'{address}🕐{shift_time}\n🔴Дата: {shift_start_date} - {shift_end_date}{salary}\n')

            print('sent')


        
