from datetime import datetime

from projdocbot import bot, get_user, seminars, next_sem_num


def process_event_yes_step(message):
    user = get_user(message)
    msg_text = message.text.lower()

    remained = int((user.start_test_dt - datetime.now()).seconds / 60)

    bot.send_message(user.uid,
                     'Вот ссылка на материал для подготовки:'
                     f'\n\n{seminars[next_sem_num[user.group]].content}\n\n'
                     f'Готовься, тест начнется через {remained} минут')
    bot.register_next_step_handler(message, process_event_yes_step)


from projdocbot.steps.test import process_test_step
from projdocbot.steps.event import process_event_step
