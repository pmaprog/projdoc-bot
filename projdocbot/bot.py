import os
import pickle
import time
import json
import logging
import requests
from types import SimpleNamespace
from requests.exceptions import TooManyRedirects
import threading
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

from telebot import types

from pprint import pprint as pp

# telebot.logger.setLevel(logging.DEBUG)

from projdocbot import (bot, users, get_user, next_sem, seminars_dates,
                        seminars, GROUPS, stop)
from projdocbot.mongo import User
from projdocbot.steps.event import process_event_step
from projdocbot.steps.schedule import process_schedule_step
from projdocbot.steps.login import process_email_step
from projdocbot.steps.settings import process_settings_step


def is_logged_in(m):
    user = get_user(m)
    return user and user.uid in users


def load_cookies():
    for u in User.objects:
        if u.cookies is not None:
            users[u.uid] = SimpleNamespace(
                session=requests.session(),
                question=None,
                answers=[]
            )
            cookies = requests.utils.cookiejar_from_dict(json.loads(u.cookies))
            users[u.uid].session.cookies.update(cookies)


def get_session(email='mpodkolzin@edu.hse.ru', password='SuperPassword'):
    session = requests.session()
    session.post('https://online.hse.ru/login/index.php',
                 data={'username': email,
                       'password': password})
    return session


def remind_about_seminar(group):
    sem_num, sem = next_sem[group]
    sem_date = seminars_dates[sem_num][group]

    remained = (sem_date.date() - datetime.now().date()).days
    if remained > 7:
        return

    for u in User.objects(uid__in=users.keys(), group=group):
        if (u.seminars[sem_num].success_date is None
                and datetime.now() >= u.remind_date):
            u.remind_date = datetime.now() + timedelta(minutes=30)
            u.seminars[next_sem[u.group][0]].notifications_count += 1
            u.save()

            kb = types.ReplyKeyboardMarkup()
            kb.row('Да', 'Напомни мне через...')
            reply = f'Через {remained} дней ({sem_date.strftime("%d.%m.%Y")}) состоится семинар на тему\n\n"{sem["theme"]}",\n\nхочешь подготовиться и пройти тест?'
            sent = bot.send_message(u.uid, reply, reply_markup=kb)
            bot.clear_step_handler_by_chat_id(u.uid)
            bot.register_next_step_handler(sent, process_event_step)


def update_seminars():
    """
    Заполняет словарь с расписанием семинаров
    """

    # todo: вынести в отдельную функцию
    global bot_session
    try:
        schedule_response = bot_session.get('https://online.hse.ru/mod/page/view.php?id=123827')
    except TooManyRedirects:
        bot_session = get_session()
        schedule_response = bot_session.get('https://online.hse.ru/mod/page/view.php?id=123827')
    schedule_soup = BeautifulSoup(schedule_response.text, features='lxml')

    rows = schedule_soup.table.tbody.find_all('tr')
    for r in rows:
        tds = r.find_all('td')
        sem_num = r.th.text
        if sem_num != '' and tds[0].text != '':
            seminars[sem_num] = {
                'theme': tds[5].text,
                'content': tds[6].text,
                # 'test': tds[7].text
            }
            seminars_dates[sem_num] = {
                '1': datetime.strptime(tds[0].text, '%d.%m.%y'),
                '2': datetime.strptime(tds[1].text, '%d.%m.%y'),
                '3': datetime.strptime(tds[2].text, '%d.%m.%y'),
                '4': datetime.strptime(tds[3].text, '%d.%m.%y'),
                '5': datetime.strptime(tds[4].text, '%d.%m.%y')
            }

    # todo: filter
    # upcoming_seminars = filter()
    for g in GROUPS:
        next_sem_num = min(seminars_dates.items(), key=lambda x: x[1][g])[0]
        # if g in next_sem:
        #     if next_sem_num != next_sem[g][0]:
        next_sem[g] = (next_sem_num, seminars[next_sem_num])


def timer():
    tick = 0
    while not stop:
        time.sleep(1)
        tick += 1

        if tick % 5 == 0:
            for g in GROUPS:
                remind_about_seminar(g)
        elif tick % (30 * 60) == 0:
            update_seminars()
            tick = 0  # нужно обнулять, а то будет переполнение


@bot.message_handler(commands=['login'])
def login(message):
    user = get_user(message)

    if is_logged_in(message):
        bot.send_message(user.uid, 'Ты уже авторизован!')
        return

    bot.send_message(user.uid, 'Введи Email')
    bot.register_next_step_handler(message, process_email_step)


@bot.message_handler(commands=['logout'])
def logout(message):
    user = get_user(message)

    if is_logged_in(message):
        del users[user.uid]
        user.cookies = None
        user.save()
        bot.send_message(user.uid, 'Ты разлогинился', reply_markup=types.ReplyKeyboardRemove())
    else:
        bot.send_message(user.uid, 'Ты не залогинен')


@bot.message_handler(func=is_logged_in)
def logged_in_handler(message):
    user = get_user(message)
    msg_text = message.text.lower()

    if msg_text == 'страница курса':
        bot.send_message(user.uid, 'https://online.hse.ru/course/view.php?id=1845')

    elif msg_text == 'расписание модуля':
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
        user.seminars[next_sem[user.group][0]].success_date = None
        user.save()
        bot.send_message(user.uid, 'Сбросили')

    elif msg_text == 'debug: отправить уведомление':
        user.remind_date = datetime.now()
        user.save()
        remind_about_seminar(user.group)

    else:
        bot.send_message(user.uid, 'Используй меню')


@bot.message_handler(func=lambda m: not is_logged_in(m))
def not_logged_in_handler(message):
    user = get_user(message)
    bot.send_message(user.uid, 'Напиши /login, чтобы залогиниться')


def main():
    global bot_session
    global stop

    try:
        load_cookies()
        try:
            bot_session = users[list(users.keys())[0]].session
        except:
            bot_session = get_session()

        update_seminars()
        threading.Thread(target=timer).start()

        print('Start polling...')
        bot.polling()
    finally:
        stop = True
        print('End polling...')
