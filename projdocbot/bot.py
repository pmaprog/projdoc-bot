import time
import json
import logging
import requests
from types import SimpleNamespace
from requests.exceptions import TooManyRedirects
import threading
from datetime import datetime, timedelta

from telebot import types

from pprint import pprint as pp

# telebot.logger.setLevel(logging.DEBUG)

import projdocbot
from projdocbot import (bot, sessions, get_user, next_sem_num, sh, tests,
                        setup_chat_logger)
from projdocbot.mongo import User, UserStatistics
from projdocbot.timer import timer, update_seminars, remind_about_seminar

from projdocbot.steps.schedule import process_schedule_step
from projdocbot.steps.login import process_email_step
from projdocbot.steps.settings import process_settings_step


def is_logged_in(m):
    return m.from_user.id in sessions


def load_sessions():
    for u in User.objects:
        if u.cookies is not None:
            sessions[u.uid] = SimpleNamespace(
                email=u.email,
                session=requests.session(),
                test=None,
                question=0,
                answers=[],
                correct=0,
                url=None,
                logger=setup_chat_logger(u.email, u.email + '.log')
            )
            cookies = requests.utils.cookiejar_from_dict(json.loads(u.cookies))
            sessions[u.uid].session.cookies.update(cookies)


def get_session(email='mpodkolzin@edu.hse.ru', password='SuperPassword'):
    session = requests.session()
    session.post('https://online.hse.ru/login/index.php',
                 data={'username': email,
                       'password': password})
    return session


def load_tests():
    rows = sh.worksheet('Тест').get_all_values()
    cur_sem = None
    for cols in rows:
        if cols[1] == '':
            cur_sem = cols[0]
            tests[cur_sem] = SimpleNamespace(questions=[], choices=[])
        else:
            cols = [i for i in cols if i != '']
            tests[cur_sem].questions.append(cols[0])
            tests[cur_sem].choices.append(cols[1:])


@bot.middleware_handler(update_types=['message'])
def log_msg(bot_instance, m):
    uid = m.chat.id
    if uid in sessions:
        user = get_user(m)
        sessions[uid].logger.info(m.text, extra={'sem_num': next_sem_num[user.group]})


@bot.message_handler(commands=['start'])
def login(message):
    uid = message.from_user.id

    if is_logged_in(message):
        bot.send_message(uid, 'Ты уже авторизован!')
        return

    bot.send_message(uid, 'Введи Email')
    bot.register_next_step_handler(message, process_email_step)


# todo: deprecated
@bot.message_handler(commands=['logout'])
def logout(message):
    uid = message.from_user.id

    if is_logged_in(message):
        user = get_user(message)
        user.cookies = None
        user.save()
        del sessions[uid]
        bot.send_message(uid, 'Ты разлогинился', reply_markup=types.ReplyKeyboardRemove())
    else:
        bot.send_message(uid, 'Ты не залогинен')


@bot.message_handler(commands=['exc'])
def debug_exception(message):
    raise Exception('debug')


@bot.message_handler(func=is_logged_in)
def logged_in_handler(message):
    user = get_user(message)
    msg_text = message.text.lower()

    if msg_text == 'страница курса':
        bot.send_message(user.uid, 'https://online.hse.ru/course/view.php?id=1845')

    elif msg_text == 'расписание':
        kb = types.ReplyKeyboardMarkup()
        (kb.row('БИВ171'), kb.row('БИВ172'), kb.row('БИВ173'), kb.row('БИВ174'), kb.row('БИВ175'), kb.row('Назад'))
        bot.send_message(user.uid, 'Выбери группу', reply_markup=kb)
        bot.register_next_step_handler(message, process_schedule_step)

    elif msg_text == 'текущие оценки':
        bot.send_message(user.uid, 'https://online.hse.ru/grade/report/user/index.php?id=1845')

    elif msg_text == 'изменить время ежедневного уведомления':
        kb = types.ReplyKeyboardMarkup()
        kb.row('9:00', '10:00', '11:00', '12:00')
        kb.row('Назад')

        chosen_time = user.chosen_time.strftime('%H:%M')

        bot.send_message(user.uid,
                         ('Выбери когда ты хочешь получать ежедневное уведомление?\n'
                          f'Сейчас ты получаешь уведомление в {chosen_time}'),
                         reply_markup=kb)
        bot.register_next_step_handler(message, process_settings_step)

    elif msg_text == 'debug: сбросить тест':
        user.seminars[next_sem_num[user.group]].success_date = None
        user.save()
        bot.send_message(user.uid, 'Сбросили')

    elif msg_text == 'debug: отправить уведомление':
        user.notify_dt = datetime.now()
        user.save()
        remind_about_seminar(user.group)

    else:
        bot.send_message(user.uid, 'Используй меню')


@bot.message_handler(func=lambda m: not is_logged_in(m))
def not_logged_in_handler(message):
    bot.send_message(message.from_user.id, 'Напиши /start, чтобы войти в систему и включить напоминания о предстоящих семинарах')


def main():
    load_sessions()
    load_tests()
    update_seminars()

    while True:
        try:
            projdocbot.stop = False
            threading.Thread(target=timer).start()

            print('Start polling...')
            bot.load_next_step_handlers()
            bot.polling(none_stop=True)
            projdocbot.stop = True
            break
        except Exception as e:
            print(e)
            projdocbot.stop = True
            time.sleep(10)
        finally:
            print('End polling...')
