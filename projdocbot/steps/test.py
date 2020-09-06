from datetime import datetime, timedelta

from telebot import types

from projdocbot import (bot, get_user, users, next_sem_num, menu)
from projdocbot.mongo import Test


def start_test(user):
    test = Test.objects(n=next_sem_num[user.group]).first()

    user.start_test_dt = None
    user.save()

    m = bot.send_message(user.uid, 'Тест начался\nУ тебя есть 10 минут')
    kb = types.ReplyKeyboardMarkup()
    for c in test.choices[0]:
        kb.row(c)
    bot.send_message(user.uid, test.questions[0], reply_markup=kb)
    bot.clear_step_handler_by_chat_id(user.uid)
    bot.register_next_step_handler(m, process_test_step)


def process_test_step(m):
    user = get_user(m)
    sem_num = next_sem_num[user.group]
    test = Test.objects(n=sem_num).first()

    q = users[user.uid].question  # номер текущего вопроса

    if m.text not in test.choices[q]:
        bot.send_message(user.uid, 'Используй меню')
        bot.register_next_step_handler(m, process_test_step)
        return

    users[user.uid].answers.append(test.choices[q].index(m.text))

    if q+1 == len(test.questions):  # если ответил на последний вопрос
        correct = 0
        for i, ans in enumerate(users[user.uid].answers):
            if test.answers[i] == ans:
                correct += 1

        bot.send_message(user.uid, f'Ты набрал {correct} из {len(test.questions)} баллов', reply_markup=menu)

        if correct / len(test.questions) <= 0.5:
            bot.send_message(user.uid, 'Тест провален\nТы сможешь попробовать еще раз сдать тест через 2 часа')
            user.remind_date = datetime.now() + timedelta(hours=2)
            # todo
        else:
            bot.send_message(user.uid, 'Молодец!\nТы успешно сдал тест')
            user.seminars[sem_num].success_date = datetime.now()

        users[user.uid].question = 0
        users[user.uid].answers = []

        user.seminars[sem_num].correct_answers_lst.append(correct)
        user.save()

        return

    kb = types.ReplyKeyboardMarkup()
    for choice in test.choices[q+1]:
        kb.row(choice)
    bot.send_message(user.uid, test.questions[q+1], reply_markup=kb)
    bot.register_next_step_handler(m, process_test_step)

    users[user.uid].question += 1


from projdocbot.steps.event import process_event_step
