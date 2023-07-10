import requests as requests

from .exceptions import VerificationFailedException, RegistrationFailedException, UnauthorizedNeedToCreateException


def post_request_proxy(url, json, headers=None):
    response = requests.post(url, json=json, headers=headers)
    print(json)
    print(response.status_code)
    print(response.json())
    return response


def get_request_proxy(url, headers=None):
    response = requests.get(url, headers=headers)
    print(url)
    print(response.status_code)
    print(response.json())
    return response


class JumisGo:
    def __init__(self, host):
        self.host = host
        self.token = None

    def get_vacancies(self):
        current_page = 1
        last_page = 999
        vacancies_to_notify = []
        while current_page < last_page:
            url = self.host + f'/api/vacancy/get?page={current_page}'
            response = requests.get(url)
            last_page = response.json()['last_page']
            current_page += 1
            vacancies = response.json()['data']
            vacancies_to_notify.extend(vacancies)
        return vacancies_to_notify

    def get_vacancy(self, id):
        url = self.host + f'/api/vacancy/get/?id={id}'
        response = requests.get(url)
        return response.json()

    def get_user_id_by_phone(self, phone):
        url = self.host + f'/api/auth/check/phone?phone={phone}'
        response = get_request_proxy(url)
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

    def user_register(self, name, phone, city, password, token, iin):
        url = self.host + '/api/auth/register'
        data = {
            'name': name,
            'phone': phone,
            'city_id': city,
            'password': password,
            'password_confirmation': password,
            'token': token,
            'doc_iin': iin
        }
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        response = post_request_proxy(url, json=data, headers=headers)
        if response.status_code != 200:
            raise RegistrationFailedException(response.json())
        return response.json()

    def accept_vacancy(self, vacancy_id):
        if self.token is None:
            raise UnauthorizedNeedToCreateException
        url = self.host + '/api/employee/vacancy/accept'
        data = {'vacancy_id': vacancy_id}
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }
        response = post_request_proxy(url, json=data, headers=headers)
        return response.json()

    def login(self, phone_number, password):
        url = self.host + '/api/auth/login'
        data = {'phone': phone_number, 'password': password}
        response = post_request_proxy(url, json=data)
        self.token = response.json()['access_token']
        return

    def logout(self):
        self.token = None
        return

