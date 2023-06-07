import datetime
import os
import sys

from telegram import KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from dotenv import load_dotenv

from .models import Employee, JobRequestAssignment, EmployeeGeoPosition, Shift
from geopy.distance import geodesic as GD
from django.db.models import Q

load_dotenv()

token = os.getenv('TELEGRAM_TOKEN')
updater = Updater(token)


def main_func(update, context):
    chat = update.effective_chat
    has_contact_in_message = hasattr(update, 'message') and hasattr(update.message, 'contact') and hasattr(update.message.contact, 'phone_number')
    if not Employee.objects.filter(chat_id=chat.id).exists() and not has_contact_in_message:
        phone_button = KeyboardButton(text='Отправить номер телефона', request_contact=True)
        context.bot.send_message(chat_id=chat.id,
                                 text=f'Пожалуйста, отправьте мне свой номер телефона для регистрации '
                                      f'(кнопка "Отправить номер телефона")',
                                 reply_markup=ReplyKeyboardMarkup([[phone_button]], resize_keyboard=True))
        return

    if has_contact_in_message:

        phone_number = update.message.contact.phone_number
        if Employee.objects.filter(phone_number=phone_number).exists():
            employee = Employee.objects.get(phone_number=phone_number)
            employee.chat_id = chat.id
            employee.save()
        else:
            Employee.objects.create(chat_id=chat.id, phone_number=phone_number)
        location_button = KeyboardButton(text='Начать смену', request_location=True)
        context.bot.send_message(chat_id=chat.id, text='Спасибо, что поделились номером телефона!\n'
                                                       'Для начала смены нажмите кнопку "Начать смену"',
                                 reply_markup=ReplyKeyboardMarkup([[location_button]], one_time_keyboard=True,
                                                                  resize_keyboard=True))
        return

    employee = Employee.objects.get(chat_id=chat.id)
    telegram_message_date = datetime.datetime.today()
    search_date_start = telegram_message_date + datetime.timedelta(days=1)
    search_date_end = telegram_message_date - datetime.timedelta(days=1)
    filter_condition = Q(employee=employee) & (Q(job_request__date_start__lte=search_date_start) & Q(job_request__date_end__gte=search_date_end))
    possible_assignments = JobRequestAssignment.objects.filter(filter_condition).all()
    assignment = None

    for possible_assignment in possible_assignments:
        if possible_assignment.job_request.is_shift_includes_time(telegram_message_date):
            if assignment is not None:
                context.bot.send_message(chat_id=chat.id, text='У вас несколько назначений на этот день.'
                                                               '\nОбратитесь к менеджеру.')
                return
            assignment = possible_assignment
    if assignment is None:
        context.bot.send_message(chat_id=chat.id, text='Для вас не была назначена заявка на смену.'
                                                       '\nОбратитесь к менеджеру.')
        return

    shift = Shift.objects.filter(Q(assignment=assignment) & Q(shift_date=datetime.datetime.today())).first()
    if not shift:
        shift = Shift.objects.create(assignment=assignment)

    if hasattr(update, 'message') and hasattr(update.message, 'location') and update.message.location:
        geo_position = update.message.location
        employee_geo_position = EmployeeGeoPosition.objects.create(
            employee=employee, latitude=geo_position['latitude'],
            longitude=geo_position['longitude'])

        if shift.start_position is None:
            branch = assignment.job_request.branch
            distance = GD((branch.latitude, branch.longitude), (geo_position['latitude'], geo_position['longitude'])).meters

            if distance > 500:
                location_button = KeyboardButton(text='Начать смену', request_location=True)
                context.bot.send_message(chat_id=chat.id, text='Вы находитесь не на территории филиала.'
                                                               '\nПожалуйста, вернитесь в офис и отправьте геоданные еще раз',
                                         reply_markup=ReplyKeyboardMarkup([[location_button]], one_time_keyboard=True,
                                                                          resize_keyboard=True))
                return
            shift.start_position = employee_geo_position
            shift.save()
            location_button = KeyboardButton(text='Закончить смену', request_location=True)
            context.bot.send_message(chat_id=chat.id,
                                     text='Не забудьте завершить смену, нажав на кнопку "Закончить смену"',
                                     reply_markup=ReplyKeyboardMarkup([[location_button]], one_time_keyboard=True,
                                                                      resize_keyboard=True)
                                     )
        elif shift.end_position is None:
            branch = assignment.job_request.branch
            distance = GD((branch.latitude, branch.longitude),
                          (geo_position['latitude'], geo_position['longitude'])).meters

            if distance > 500:
                location_button = KeyboardButton(text='Закончить смену', request_location=True)
                context.bot.send_message(chat_id=chat.id, text='Вы находитесь не на территории филиала.'
                                                               '\nПожалуйста, вернитесь в офис и отправьте геоданные еще раз',
                                         reply_markup=ReplyKeyboardMarkup([[location_button]], one_time_keyboard=True,
                                                                          resize_keyboard=True))
                return

            shift.end_position = employee_geo_position
            shift.save()
            context.bot.send_message(chat_id=chat.id, text='Спасибо за отметку, ваши данные записаны и отправлены работодателю.',
                                     reply_markup=ReplyKeyboardMarkup([[]]))
        else:
            context.bot.send_message(chat_id=chat.id, text='Все уже заполнено, спасибо!')

        return

    # Fallback to unsupported message
    elif shift.start_position is None:
        location_button = KeyboardButton(text='Начать смену', request_location=True)
        context.bot.send_message(chat_id=chat.id,
                                 text=f'Для начала смены нажмите кнопку "Начать смену"',
                                 reply_markup=ReplyKeyboardMarkup([[location_button]], one_time_keyboard=True,
                                                                  resize_keyboard=True))
    elif shift.end_position is None:
        location_button = KeyboardButton(text='Закончить смену', request_location=True)
        context.bot.send_message(chat_id=chat.id,
                                 text=f'Не забудьте завершить смену, нажав на кнопку "Закончить смену"',
                                 reply_markup=ReplyKeyboardMarkup([[location_button]], one_time_keyboard=True,
                                                                  resize_keyboard=True))
    else:
        context.bot.send_message(chat_id=chat.id,
                                 text=f'Мы записали Ваши данные о начале и окончании смены',)
    return


def start(update, context):
    chat = update.effective_chat
    name = update.message.chat.first_name
    context.bot.send_message(chat_id=chat.id, text=f'Спасибо, что включили меня, {name}!')
    main_func(update, context)


command = " ".join(sys.argv[:])
if 'runserver' in command or 'gunicorn' in command:
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, main_func))
    updater.dispatcher.add_handler(MessageHandler(Filters.contact, main_func))
    updater.dispatcher.add_handler(MessageHandler(Filters.location, main_func))
    updater.start_polling()
    # updater.idle()

