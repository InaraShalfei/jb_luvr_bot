import datetime
import os
import re
import sys

from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from dotenv import load_dotenv

from .models import Employee, JobRequestAssignment, EmployeeGeoPosition, Shift, JobRequest
from geopy.distance import geodesic as GD
from django.db.models import Q

load_dotenv()

token = os.getenv('TELEGRAM_TOKEN')
updater = Updater(token)


def apply_flow(update, context):
    chat = update.effective_chat
    employee = Employee.objects.get(chat_id=chat.id)

    job_request = employee.current_job_request
    default_buttons = ['Отмена', 'OK']
    # TODO 1 if no surname, add Surname button to default
    # TODO 1 if no IIN, add IIN button to default
    buttons = []
    delta = datetime.timedelta(days=1)
    job_request_date = job_request.date_start
    while job_request_date <= job_request.date_end:
        date = datetime.datetime.strftime(job_request_date, '%d.%m.%Y')
        buttons.append(date)
        job_request_date += delta

    text = update.message.text
    #TODO 3 if status=waiting for IIN, employee.IIN=text, status=empty, send_msg=continue, delete IIN button, if IIN is invalid, status not changed
    # TODO 3 if status=waiting for surname, employee.surname=text, status=empty, delete surname button


    if text.startswith('/start jobrequest'):
        name = update.message.chat.first_name
        context.bot.send_message(chat_id=chat.id, text=f'Добрый день, {name}')
        context.bot.send_message(
            chat_id=chat.id,
            text=f'Хотите записаться на должность {job_request.employee_position}?\nПожалуйста, выберите даты и нажмите ОК',
            reply_markup=ReplyKeyboardMarkup([buttons, default_buttons], one_time_keyboard=True,
                                             resize_keyboard=True)
        )
        return
    #TODO 2 if text is IIN, status to waiting for IIN, send_mesg = Write IIN
    # TODO 2 if text is surname, status to waiting for surname, send_mesg = Write surname
    elif text == 'Отмена':
        employee.job_request_draft = None
        employee.save()
        context.bot.send_message(
            chat_id=chat.id,
            text=f'Все выбранные даты были удалены. Выберите даты снова',
            reply_markup=ReplyKeyboardMarkup([buttons, default_buttons], one_time_keyboard=True,
                                             resize_keyboard=True)
        )
        return

    elif text == 'OK':
        real_assigned_dates = []
        for date in employee.job_request_draft.split():
            shift_date = datetime.datetime.strptime(date, '%d.%m.%Y')
            assignment = (JobRequestAssignment.objects.get(job_request=job_request, employee=employee, assignment_date=shift_date)
                          if JobRequestAssignment.objects.filter(job_request=job_request, employee=employee, assignment_date=shift_date).exists()
                          else None)
            if not assignment:
                real_assigned_dates.append(shift_date)
                JobRequestAssignment.objects.create(job_request=job_request, employee=employee, assignment_date=shift_date)
            else:
                context.bot.send_message(
                    chat_id=chat.id,
                    text=f'На дату {date} уже найден сотрудник',
                )
        employee.current_job_request = None
        employee.job_request_draft = None
        employee.save()
        if real_assigned_dates:
            dates = [datetime.datetime.strftime(date, '%d.%m.%Y') for date in real_assigned_dates]
            context.bot.send_message(
                chat_id=chat.id,
                text=f'Для вас на должность {job_request.employee_position} были созданы назначения на следующие даты: {" ".join(dates)}',
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            context.bot.send_message(
                chat_id=chat.id,
                text='На данные даты уже найдены сотрудники. Проверьте другие даты или вакансии',
                reply_markup=ReplyKeyboardRemove()
            )
        return
    elif re.compile(r"(^\d{2}.\d{2}.\d{4}$)").match(text):
        if not employee.job_request_draft:
            employee.job_request_draft = text
            employee.save()
        else:
            dates = employee.job_request_draft.split()
            dates.append(text)
            dates.sort()
            employee.job_request_draft = ' '.join(dates)
            employee.save()

        busy_dates = employee.job_request_draft.split() if employee.job_request_draft else []
        buttons = list(set(buttons) - set(busy_dates))
        buttons.sort()
        context.bot.send_message(
            chat_id=chat.id,
            text=f'Вы выбрали {employee.job_request_draft}. Хотите выбрать еще смены?\nПожалуйста, выберите даты и нажмите ОК',
            reply_markup=ReplyKeyboardMarkup([buttons, default_buttons], one_time_keyboard=True, resize_keyboard=True)
        )
        return
    else:
        busy_dates = employee.job_request_draft.split() if employee.job_request_draft else []
        buttons = list(set(buttons) - set(busy_dates))
        buttons.sort()
        intro_text = f'Вы выбрали {employee.job_request_draft}. Хотите выбрать еще смены?\n' if employee.job_request_draft else ''
        context.bot.send_message(
            chat_id=chat.id,
            text=f'{intro_text}Пожалуйста, выберите даты и нажмите ОК',
            reply_markup=ReplyKeyboardMarkup([buttons, default_buttons], one_time_keyboard=True, resize_keyboard=True)
        )


def main_func(update, context):
    chat = update.effective_chat
    employee = Employee.objects.get(chat_id=chat.id) if Employee.objects.filter(chat_id=chat.id).exists() else None
    if employee and employee.current_job_request:
        return apply_flow(update, context)
    has_contact_in_message = hasattr(update, 'message') and hasattr(update.message, 'contact') and hasattr(
        update.message.contact, 'phone_number')
    if not employee and not has_contact_in_message:
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
        if possible_assignment.is_shift_includes_time(datetime.datetime.now()):
            if assignment is not None:
                context.bot.send_message(chat_id=chat.id, text='У вас несколько назначений на этот день.'
                                                               '\nОбратитесь к менеджеру.')
                return
            assignment = possible_assignment
    if assignment is None:
        context.bot.send_message(chat_id=chat.id, text='Для вас не была назначена заявка на смену.'
                                                       '\nЛибо вы пришли слишком рано, ваша смена еще не началась')
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
            context.bot.send_message(chat_id=chat.id,
                                     text='Не забудьте завершить смену, нажав на кнопку "Закончить смену"',
                                     )
            location_button = KeyboardButton(text='Закончить смену', request_location=True)
            shift_time_end = datetime.time.strftime(shift.assignment.job_request.shift_time_end, '%H:%M')
            context.bot.send_message(chat_id=chat.id,
                                     text=f'Вы уверены, что хотите закончить смену? Смена закончится в {shift_time_end}',
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
    text: str = update.message.text
    if text.startswith('/start jobrequest'):
        job_request_id = int(text.replace('/start jobrequest', ''))
        job_request = JobRequest.objects.get(pk=job_request_id)
        employee, created = Employee.objects.get_or_create(chat_id=chat.id)
        employee.current_job_request = job_request
        employee.save()
        apply_flow(update, context)

    else:
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

