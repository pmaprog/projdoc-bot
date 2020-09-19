from datetime import datetime, timedelta

from telebot import types

from projdocbot import bot, get_user, seminars, next_sem_num, sessions
from projdocbot.mongo import Url


def process_event_step(message):
    user = get_user(message)
    msg_text = message.text.lower()

    if msg_text == 'да':
        user.notify_dt = None
        user.start_test_dt = datetime.now() + timedelta(minutes=30)
        # user.start_test_dt = datetime.now() + timedelta(seconds=5)
        user.save()

        sem_num = next_sem_num[user.group]
        if len(user.seminars[sem_num].correct_answers_lst) > 0:
            start_test(user)
            return

        url = Url(uid=user.uid, sem_num=sem_num,
                  url=seminars[next_sem_num[user.group]].content)
        url.save()

        sessions[user.uid].url = f'http://projdoc.auditory.ru/{url.key}'

        kb = types.ReplyKeyboardRemove()
        bot.send_message(user.uid,
                         'Вот ссылка на материал для подготовки:'
                         # f'\n\n{seminars[next_sem_num[user.group]].content}\n\n'
                         f'\n\n{sessions[user.uid].url}\n\n'
                         'Готовься, тест начнется через 30 минут',
                         reply_markup=kb)
        bot.register_next_step_handler(message, process_event_yes_step)

    elif msg_text == 'напомни мне через...':
        kb = types.ReplyKeyboardMarkup()
        kb.row('Через час', 'Через 2 часа', 'Через 4 часа')
        kb.row('Через 8 часов', 'Завтра', 'Через 3 секунды')
        bot.send_message(user.uid, 'Через сколько времени тебе напомнить?', reply_markup=kb)
        bot.register_next_step_handler(message, process_choose_time_step)

    else:
        bot.send_message(user.uid, 'Используй меню')
        bot.register_next_step_handler(message, process_event_step)


from projdocbot.steps.event_yes import process_event_yes_step
from projdocbot.steps.choose_time import process_choose_time_step
from projdocbot.steps.test import start_test
