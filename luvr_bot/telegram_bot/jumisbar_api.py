import datetime

import requests as requests

from .exceptions import VerificationFailedException, RegistrationFailedException


def post_request_proxy(url, json, headers=None):
    response = requests.post(url, json=json, headers=headers)
    print(json)
    print(response.status_code)
    print(response.json())
    return response


class JumisGo:
    def __init__(self, host):
        self.host = host

    def get_vacancies(self, bot, channels):
        url = self.host + '/api/vacancy/get'
        response = requests.get(url)
        vacancies = response.json()['data']
        for vacancy in vacancies:
            branch = vacancy['branch_description']
            address = vacancy['branch_address']
            position = vacancy['title']
            rate = vacancy['rate_hour']
            text1 = f'{branch} - {address}\n📌{position}\n'
            text2 = f'✅Оплата: {rate} тнг/час\nhttp://t.me/jb_luvr_bot'

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
                if position in channels:
                    bot.send_message(chat_id=channels[position], text=f'{text1}🕐{shift_time}\n🔴Дата: {shift_start_date} - {shift_end_date}{text2}\n')

    def get_user_id_by_phone(self, phone):
        url = self.host + f'/api/auth/check/phone?phone={phone}'
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()['user_id']
        return None

    def get_existing_languages(self):
        url = self.host + '/api/language/get'
        response = requests.get(url)
        languages = response.json()['data']
        return languages

    def get_existing_cities(self):
        url = self.host + '/api/city/get'
        response = requests.get(url)
        cities = response.json()['data']
        return cities

    def request_phone_verification(self, phone):
        url = self.host + '/api/auth/send/token'
        data = {'phone': phone}
        response = post_request_proxy(url, json=data)
        if response.status_code != 200:
            raise VerificationFailedException

    def user_register(self, name, phone, city, password, token):
        url = self.host + '/api/auth/register'
        data = {
            'name': name,
            'phone': phone,
            'city_id': city,
            'password': password,
            'disability_group': False,
            'password_confirmation': password,
            'token': token
        }
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        response = post_request_proxy(url, json=data, headers=headers)
        if response.status_code != 200:
            raise RegistrationFailedException(response.json())
        return response.json()


