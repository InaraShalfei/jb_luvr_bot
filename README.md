# jb_luvr_bot
# Celery commands:
- запустить RabbitMQ с помощью команды docker run -d -p 5672:5672 bitnami/rabbitmq:latest
- запустить Celery task с помощью команды export DJANGO_SETTINGS_MODULE="luvr_bot.settings"; celery -A luvr_bot worker --loglevel=DEBUG
- запустить Celery beat с помощью команды export DJANGO_SETTINGS_MODULE="luvr_bot.settings"; celery -A luvr_bot beat --loglevel=DEBUG
