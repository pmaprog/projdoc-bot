import random
from datetime import datetime, timedelta

from telebot import types

from projdocbot import (bot, get_user, sessions, next_sem_num, menu, tests)


def send_question(user, q):
    sem_num = next_sem_num[user.group]
    test = tests[sem_num]
    kb = types.ReplyKeyboardMarkup()
    choices = list(test.choices[q])
    random.shuffle(choices)
    for c in choices:
        kb.row(c)
    bot.send_message(user.uid, test.questions[q], reply_markup=kb)


def start_test(user):
    user.start_test_dt = None
    # user.stop_test_dt = datetime.now() + timedelta(seconds=5)
    user.stop_test_dt = datetime.now() + timedelta(minutes=10)
    user.save()

    sessions[user.uid].test = next_sem_num[user.group]
    sessions[user.uid].question = 0
    sessions[user.uid].correct = 0
    sessions[user.uid].answers = []
    sessions[user.uid].url = None

    m = bot.send_message(user.uid, 'Тест начался\nУ тебя есть 10 минут')
    send_question(user, 0)
    bot.clear_step_handler_by_chat_id(user.uid)
    bot.register_next_step_handler(m, process_test_step)


def stop_test(user):
    sem_num = sessions[user.uid].test
    test = tests[sem_num]

    if datetime.now() >= user.stop_test_dt:
        bot.send_message(user.uid, 'Время истекло')

    bot.send_message(user.uid, f'Ты набрал {sessions[user.uid].correct} из {len(test.questions)} баллов', reply_markup=menu)

    if sessions[user.uid].correct / len(test.questions) <= 0.5:
        bot.send_message(user.uid, 'Тест провален\nТы сможешь попробовать еще раз сдать тест через 2 часа')
        user.notify_dt = datetime.now() + timedelta(hours=2)
    else:
        bot.send_message(user.uid, 'Молодец!\nТы успешно сдал тест')
        user.notify_tommorow()
        user.seminars[sem_num].success_date = datetime.now()

    user.seminars[sem_num].correct_answers_lst.append(sessions[user.uid].correct)
    user.stop_test_dt = None
    user.save()

    bot.clear_step_handler_by_chat_id(user.uid)


def process_test_step(m):
    user = get_user(m)
    test = tests[sessions[user.uid].test]

    q = sessions[user.uid].question  # номер текущего вопроса

    if m.text not in test.choices[q]:
        bot.send_message(user.uid, 'Используй меню')
        bot.register_next_step_handler(m, process_test_step)
        return

    if test.choices[q][0] == m.text:
        sessions[user.uid].correct += 1

    if q+1 == len(test.questions):  # если ответил на последний вопрос
        stop_test(user)
    else:
        remaining_time = user.stop_test_dt - datetime.now()
        m, s = int(remaining_time.seconds / 60), remaining_time.seconds % 60

        bot.send_message(user.uid, f'Осталось времени: {m}:{s:02d}')
        send_question(user, q+1)
        bot.register_next_step_handler(m, process_test_step)

        sessions[user.uid].question += 1
