import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

user = os.getenv('RABBITMQ_USERNAME')
password = os.getenv('RABBITMQ_PASSWORD')
app = Celery(
    'luvr_bot',
    broker=f'amqp://{user}:{password}@localhost',
    include=['luvr_bot.tasks']
)

if __name__ == '__main__':
    app.start()

# How to run:
# 1. Ensure you're in `jb_luvr_bot` dir
# 2. `cd luvr_bot`
# 3. export `DJANGO_SETTINGS_MODULE="luvr_bot.settings"; celery -A luvr_bot worker --loglevel=DEBUG`
# 4. Open new terminal.
# 5. Ensure you're in `jb_luvr_bot` dir
# 6. `cd luvr_bot`
# 7. export `DJANGO_SETTINGS_MODULE="luvr_bot.settings"; celery -A luvr_bot beat --loglevel=DEBUG`