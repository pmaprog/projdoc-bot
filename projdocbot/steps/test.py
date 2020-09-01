from datetime import datetime
from string import ascii_lowercase, ascii_uppercase

from telebot import types

from projdocbot import (bot, get_user, users, next_sem, menu)
from projdocbot.mongo import Test


def process_test_step(message):
    user = get_user(message)
    msg_text = message.text.lower()
    sem_num = next_sem[user.group][0]
    test = Test.objects(n=sem_num).first()

    users[user.uid].question = users[user.uid].question or 0
    q = users[user.uid].question  # номер текущего вопроса

    if ((msg_text == 'начать тест' and q != 0)
            or (msg_text != 'начать тест' and msg_text not in list(ascii_lowercase[:len(test.questions)]))):
        bot.send_message(user.uid, 'Используй меню')
        bot.register_next_step_handler(message, process_test_step)
        return

    if msg_text != 'начать тест':
        users[user.uid].answers.append(msg_text)

    if q == len(test.questions):  # если ответил на последний вопрос
        correct = 0
        for i, ans in enumerate(users[user.uid].answers):
            if test.answers[i] == ans:
                correct += 1

        bot.send_message(user.uid, f'Ты набрал {correct} из {len(test.questions)} баллов', reply_markup=menu)

        if correct / len(test.questions) <= 0.5:
            bot.send_message(user.uid, 'Попробуй еще раз в следующий раз')
            message.text = 'напомни мне через...'
            process_event_step(message)
        else:
            bot.send_message(user.uid, 'Молодец!\nТы успешно сдал тест')
            user.seminars[sem_num].success_date = datetime.now()

        users[user.uid].question = None
        users[user.uid].answers = []

        user.seminars[sem_num].attempts += 1
        user.save()

        return

    reply = f'{test.questions[q]}\n\n'
    kb = types.ReplyKeyboardMarkup()
    for i, choice in enumerate(test.choices[q]):
        letter = ascii_uppercase[i]
        reply += f'{letter}. {choice}\n'
        kb.row(letter)
    bot.send_message(user.uid, reply, reply_markup=kb)
    bot.register_next_step_handler(message, process_test_step)

    users[user.uid].question += 1


from projdocbot.steps.event import process_event_step
