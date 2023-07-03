import datetime
import os
import re
import sys


from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from dotenv import load_dotenv

from .dictionaries import translates
from .exceptions import VerificationFailedException, RegistrationFailedException
from .jumisbar_api import JumisGo
from .models import Employee, JobRequestAssignment, EmployeeGeoPosition, Shift, JobRequest
from geopy.distance import geodesic as GD
from django.db.models import Q

load_dotenv()

token = os.getenv('TELEGRAM_TOKEN')
updater = Updater(token)


def registration_func(update, context, employee: Employee):
    chat = update.effective_chat
    text = update.message.text

    api = JumisGo('https://admin.jumisgo.kz')
    if employee.language is None:
        languages = api.get_existing_languages()
        for language in languages:
            if text == language['title']:
                employee.language = language['id']
                employee.save()
        if employee.language is None:
            context.bot.send_message(chat_id=chat.id,
                                     text=f'Тіркелу үшін тілді таңдаңыз.\nПожалуйста, выберите язык для прохождения регистрации',
                                     reply_markup=ReplyKeyboardMarkup([[language['title'] for language in languages]], resize_keyboard=True,
                                                                      one_time_keyboard=True))
            return

    has_contact_in_message = hasattr(update, 'message') and hasattr(update.message, 'contact') and hasattr(
        update.message.contact, 'phone_number')
    if (not employee or not employee.phone_number) and not has_contact_in_message:
        phone_button = KeyboardButton(text='Отправить номер телефона' if employee.language == 2 else 'Телефон нөмірін жіберіңіз',
                                      request_contact=True)
        context.bot.send_message(chat_id=chat.id,
                                 text=translates['phone_number'][employee.language],
                                 reply_markup=ReplyKeyboardMarkup([[phone_button]], resize_keyboard=True,
                                                                  one_time_keyboard=True))
        return
    if has_contact_in_message:
        phone_number = update.message.contact.phone_number
        employee.phone_number = phone_number
        employee.save()
        jumis_go_user_id = api.get_user_id_by_phone(employee.phone_number)
        if jumis_go_user_id:
            employee.jumis_go_user_id = jumis_go_user_id
            employee.save()
            context.bot.send_message(chat_id=chat.id,
                                     text=translates['already_registered'][employee.language])
        else:
            try:
                api.request_phone_verification(employee.phone_number)
                context.bot.send_message(chat_id=chat.id,
                                         text=translates['sms_code'][employee.language])
            except VerificationFailedException:
                context.bot.send_message(chat_id=chat.id,
                                         text=translates['sms_verification_failed'][employee.language])
        return
    if employee.token is None:
        regex = r'^(\d{4,6})$'
        pattern = re.compile(regex)
        if not pattern.match(text):
            context.bot.send_message(chat_id=chat.id,
                                     text=translates['sms_cod_incorrect'][employee.language])
        else:
            employee.token = text
            employee.save()
            context.bot.send_message(chat_id=chat.id,
                                     text=translates['full_name'][employee.language])
        return
    if employee.full_name is None:
        employee.full_name = text
        employee.save()
        context.bot.send_message(chat_id=chat.id,
                                 text=translates['inn'][employee.language])
        return
    if employee.INN is None:
        regex = r'^(\d{12})$'
        pattern = re.compile(regex)
        if not pattern.match(text):
            context.bot.send_message(chat_id=chat.id,
                                     text=translates['inn_incorrect'][employee.language])
        else:
            employee.INN = text
            employee.save()
            context.bot.send_message(chat_id=chat.id,
                                     text=translates['password'][employee.language])
        return

    if employee.password is None:
        password = text
        if len(password) < 8:
            context.bot.send_message(chat_id=chat.id,
                                     text=translates['password_invalid'][employee.language])
        else:
            employee.password = password
            employee.save()
            try:
                api.user_register(employee.full_name, employee.phone_number,
                                  employee.password, employee.token)
                context.bot.send_message(chat_id=chat.id,
                                         text=translates['successful_registration'][employee.language])

            except RegistrationFailedException:
                context.bot.send_message(chat_id=chat.id,
                                         text=translates['registration_failed'][employee.language])
    return


def main_func(update, context):
    chat = update.effective_chat
    employee, created = Employee.objects.get_or_create(chat_id=chat.id)

    if employee.jumis_go_user_id is None:
        return registration_func(update, context, employee)

    return


def start(update, context):
    chat = update.effective_chat
    name = update.message.chat.first_name
    context.bot.send_message(chat_id=chat.id, text=f'Спасибо, что включили меня, {name}!')
    channels_dict = {'Кассир': '@kassir_jumisbar', 'Продавец': '@prodavets_jumisbar'}
    api = JumisGo('https://admin.jumisgo.kz')
    api.get_vacancies(context.bot, channels_dict)
    main_func(update, context)


command = " ".join(sys.argv[:])
if 'runserver' in command or 'gunicorn' in command:
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, main_func))
    updater.dispatcher.add_handler(MessageHandler(Filters.contact, main_func))
    updater.dispatcher.add_handler(MessageHandler(Filters.location, main_func))
    updater.start_polling()
