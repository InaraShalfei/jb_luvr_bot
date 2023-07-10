import datetime
import math
import os
import re
import sys

import numpy as np
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from dotenv import load_dotenv

from .dictionaries import translates
from .exceptions import VerificationFailedException, RegistrationFailedException
from .jumisbar_api import JumisGo
from .models import Employee, JobRequestAssignment, EmployeeGeoPosition, Shift, JobRequest, Vacancy, Training
from geopy.distance import geodesic as GD
from django.db.models import Q

load_dotenv()

token = os.getenv('TELEGRAM_TOKEN')
updater = Updater(token)

EMPLOYEE_LANGUAGE = 'language'
EMPLOYEE_PHONE_NUMBER = 'phone_number'
EMPLOYEE_TOKEN = 'token'
EMPLOYEE_FULL_NAME = 'full_name'
EMPLOYEE_IIN = 'IIN'
EMPLOYEE_CITY = 'city'
EMPLOYEE_PASSWORD = 'password'

api = JumisGo('https://admin.jumisgo.kz')


def process_registration_error(context, error, employee: Employee):
    error_employee_field_dict = {
        'name': 'full_name',
        'password': 'password',
        'doc_iin': 'IIN',
        'token': 'token',
        'city_id': 'city',
        # 'phone': 'phone_number'
    }
    if error in error_employee_field_dict:
        context.bot.send_message(chat_id=employee.chat_id,
                                 text=translates[f'{error}_failed'][employee.language])
        setattr(employee, error_employee_field_dict[error], None)
        employee.save()
    else:
        context.bot.send_message(chat_id=employee.chat_id,
                                 text=translates['unknown_error'][employee.language])


def get_next_empty_field(employee: Employee):
    if employee.language is None:
        return EMPLOYEE_LANGUAGE
    if not employee.phone_number:
        return EMPLOYEE_PHONE_NUMBER
    if employee.token is None:
        return EMPLOYEE_TOKEN
    if employee.full_name is None:
        return EMPLOYEE_FULL_NAME
    if employee.IIN is None:
        return EMPLOYEE_IIN
    if employee.city is None:
        return EMPLOYEE_CITY
    if employee.password is None:
        return EMPLOYEE_PASSWORD
    return None


def ask(employee: Employee, next_empty_field, context):
    if next_empty_field is None:
        return False

    if next_empty_field == EMPLOYEE_LANGUAGE:
        languages = api.get_existing_languages()
        context.bot.send_message(chat_id=employee.chat_id,
                                 text=f'Тіркелу үшін тілді таңдаңыз.\nПожалуйста, выберите язык для прохождения регистрации',
                                 reply_markup=ReplyKeyboardMarkup([[language['title'] for language in languages]],
                                                                  resize_keyboard=True,
                                                                  one_time_keyboard=True))
    elif next_empty_field == EMPLOYEE_PHONE_NUMBER:
        phone_button = KeyboardButton(text='Отправить номер телефона' if employee.language == '2' else 'Телефон нөмірін жіберіңіз',
                                      request_contact=True)
        context.bot.send_message(chat_id=employee.chat_id,
                                 text=translates['phone_number'][employee.language],
                                 reply_markup=ReplyKeyboardMarkup([[phone_button]], resize_keyboard=True,
                                                                  one_time_keyboard=True))
    elif next_empty_field == EMPLOYEE_TOKEN:
        context.bot.send_message(chat_id=employee.chat_id,
                                 text=translates['sms_code'][employee.language])
    elif next_empty_field == EMPLOYEE_FULL_NAME:
        context.bot.send_message(chat_id=employee.chat_id,
                                 text=translates['full_name'][employee.language])
    elif next_empty_field == EMPLOYEE_IIN:
        context.bot.send_message(chat_id=employee.chat_id,
                                 text=translates['iin'][employee.language])
    elif next_empty_field == EMPLOYEE_CITY:
        cities = api.get_existing_cities()
        if employee.city is None:
            context.bot.send_message(chat_id=employee.chat_id,
                                     text=translates['cities'][employee.language],
                                     reply_markup=ReplyKeyboardMarkup(
                                         arrange_buttons([city['title'] for city in cities]),
                                         resize_keyboard=True,
                                         one_time_keyboard=True)
                                     )
    elif next_empty_field == EMPLOYEE_PASSWORD:
        context.bot.send_message(chat_id=employee.chat_id,
                                 text=translates['password'][employee.language])

    return True


def arrange_buttons(buttons):
    return np.array_split(buttons, math.ceil(len(buttons) / 3))


def vacancy_accept_func(update, context, employee):
    text = update.message.text

    if text == 'Да':
        api.login(employee.phone_number, employee.password)
        api.accept_vacancy(employee.vacancy_id_draft)
        return
    elif text == 'Нет':
        employee.vacancy_id_draft = None
        employee.save()
        context.bot.send_message(chat_id=employee.chat_id, text='Вы отказались от этой вакансии. Посмотрите другие вакансии')
    return


def registration_func(update, context, employee: Employee):
    chat = update.effective_chat
    text = update.message.text

    if employee.language is None:
        languages = api.get_existing_languages()
        for language in languages:
            if text == language['title']:
                employee.language = str(language['id'])
                employee.save()
        if ask(employee, get_next_empty_field(employee), context):
            return

    has_contact_in_message = hasattr(update, 'message') and hasattr(update.message, 'contact') and hasattr(
        update.message.contact, 'phone_number')
    if (not employee or not employee.phone_number) and not has_contact_in_message:
        if ask(employee, get_next_empty_field(employee), context):
            return

    if has_contact_in_message:
        phone_number = update.message.contact.phone_number
        employee.phone_number = phone_number
        employee.token = None
        employee.save()
        jumis_go_user_id = api.get_user_id_by_phone(employee.phone_number)
        jumis_go_user_id = None # todo
        if jumis_go_user_id:
            employee.jumis_go_user_id = jumis_go_user_id
            employee.save()
            context.bot.send_message(chat_id=chat.id,
                                     text=translates['already_registered'][employee.language])
            return
        try:
            api.request_phone_verification(employee.phone_number)
            if ask(employee, get_next_empty_field(employee), context):
                return
        except VerificationFailedException:
            context.bot.send_message(chat_id=chat.id,
                                     text=translates['sms_verification_failed'][employee.language])

    if employee.token is None:
        regex = r'^(\d{4,6})$'
        pattern = re.compile(regex)
        if not pattern.match(text):
            context.bot.send_message(chat_id=chat.id,
                                     text=translates['sms_cod_incorrect'][employee.language])
            return
        employee.token = text
        employee.save()
        if ask(employee, get_next_empty_field(employee), context):
            return

    if employee.full_name is None:
        name = text
        if 2 > len(name) > 100:
            context.bot.send_message(chat_id=chat.id,
                                     text=translates['name_invalid'][employee.language])
            return
        employee.full_name = name
        employee.save()
        if ask(employee, get_next_empty_field(employee), context):
            return

    if employee.IIN is None:
        regex = r'^(\d{12})$'
        pattern = re.compile(regex)
        if not pattern.match(text):
            context.bot.send_message(chat_id=chat.id,
                                     text=translates['iin_incorrect'][employee.language])
            return
        employee.IIN = text
        employee.save()
        if ask(employee, get_next_empty_field(employee), context):
            return

    if employee.city is None:
        cities = api.get_existing_cities()
        for city in cities:
            if text == city['title']:
                employee.city = int(city['id'])
                employee.save()
        if ask(employee, get_next_empty_field(employee), context):
            return

    if employee.password is None:
        password = text
        if len(password) < 6:
            context.bot.send_message(chat_id=chat.id,
                                     text=translates['password_invalid'][employee.language])
            return
        employee.password = password
        employee.save()
        if get_next_empty_field(employee) is None and employee.jumis_go_user_id is None:
            try:
                employee.jumis_go_user_id = api.user_register(employee.full_name, employee.phone_number, employee.city,
                                                              employee.password, employee.token, employee.IIN)
                employee.save()
                context.bot.send_message(chat_id=chat.id,
                                         text=translates['successful_registration'][employee.language])
                if Training.objects.filter(iin=employee.IIN).exists():
                    vacancy = api.get_vacancy(employee.vacancy_id_draft)
                    context.bot.send_message(chat_id=employee.chat_id,
                                             text=f'Вы точно хотите откликнуться на эту вакансию {vacancy["title"]}?',
                                             reply_markup=ReplyKeyboardMarkup([['Да'], ['Нет']], resize_keyboard=True,
                                                                              one_time_keyboard=True))
                    vacancy_accept_func(update, context, employee)

                return
            except RegistrationFailedException as e:
                context.bot.send_message(chat_id=chat.id,
                                         text=translates['registration_failed'][employee.language])
                print(e.args[0]['errors'])
                if 'errors' in e.args[0]:
                    errors = e.args[0]['errors']
                    for error in errors:
                        process_registration_error(context, error, employee)
                ask(employee, get_next_empty_field(employee), context)
                return


def main_func(update, context):
    # with open('logs.txt', mode='a') as f:
    #     f.write(str(update.message.text) + '\n\n')
    chat = update.effective_chat
    if chat.id < 0:
        return
    print(update)
    employee, created = Employee.objects.get_or_create(chat_id=chat.id)

    if employee.jumis_go_user_id is None:
        return registration_func(update, context, employee)
    elif Training.objects.filter(iin=employee.IIN).exists() and employee.jumis_go_user_id and employee.vacancy_id_draft:
        vacancy = api.get_vacancy(employee.vacancy_id_draft)
        context.bot.send_message(chat_id=employee.chat_id,
                                 text=f'Вы точно хотите откликнуться на эту вакансию {vacancy["title"]}?',
                                 reply_markup=ReplyKeyboardMarkup([['Да'], ['Нет']], resize_keyboard=True,
                                                                  one_time_keyboard=True))
        return vacancy_accept_func(update, context, employee)

    return


def start(update, context):
    chat = update.effective_chat
    name = update.message.chat.first_name
    text: str = update.message.text
    if text.startswith('/start vacancy'):
        vacancy_id = int(text.replace('/start vacancy', ''))
        employee, created = Employee.objects.get_or_create(chat_id=chat.id)
        employee.vacancy_id_draft = vacancy_id
        employee.save()

        print(vacancy_id)
    context.bot.send_message(chat_id=chat.id, text=f'Спасибо, что включили меня, {name}!')
    main_func(update, context)


command = " ".join(sys.argv[:])
if 'runserver' in command or 'gunicorn' in command:
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, main_func))
    updater.dispatcher.add_handler(MessageHandler(Filters.contact, main_func))
    updater.dispatcher.add_handler(MessageHandler(Filters.location, main_func))
    updater.start_polling()
