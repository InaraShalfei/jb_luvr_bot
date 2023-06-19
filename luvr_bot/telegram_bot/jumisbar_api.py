import requests as requests


class JumisGo:
    def __init__(self, host):
        self.host = host

    def get_vacancies(self, bot, channels):
        url = self.host + '/api/vacancy/get'
        print(url)
        response = requests.get(url)
        print(response.text)
        vacancies = response.json()['data']
        for vacancy in vacancies:
            branch = vacancy['branch_description']
            address = vacancy['branch_description'] + vacancy['branch_address']
            position = vacancy['title']
            rate = vacancy['rate_hour']
            text1 = f'{branch} - {address}\n📌{position}\n🕐'
            text2 = f'✅Оплата: {rate} тнг/час\nt.me/@jb_luvr_bot?start=jobrequest'

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
                shift_start_date = sorted_dates[0]
                shift_end_date = sorted_dates[-1]
                bot.send_message(chat_id=channels[position], text=f'{text1}🕐{shift_time}\n🔴Дата: {shift_start_date} - {shift_end_date}{text2}')




