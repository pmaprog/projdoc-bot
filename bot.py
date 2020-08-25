import os
import pickle
import time
import json
import logging
import requests
from requests.exceptions import TooManyRedirects
import threading
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from mongo import User

import telebot
from telebot import types

# telebot.logger.setLevel(logging.DEBUG)

bot = telebot.TeleBot(os.getenv('PROJDOC_TOKEN'))
sessions = {}
seminars = {}
stop = False
bot_session = None

menu = types.ReplyKeyboardMarkup()
menu.row('Страница курса')
menu.row('Расписание модуля')
menu.row('Текущие оценки')
menu.row('Изменить время ежедневного уведомления')


def get_user(message):
    user = User.objects(uid=message.from_user.id).first()

    if not user:
        user = User(uid=message.from_user.id)
        user.save()

    return user


def is_logged_in(m):
    user = get_user(m)
    return user and user.uid in sessions


def load_cookies():
    for u in User.objects:
        if u.cookies is not None:
            sessions[u.uid] = requests.session()
            cookies = requests.utils.cookiejar_from_dict(json.loads(u.cookies))
            sessions[u.uid].cookies.update(cookies)


def get_session(email='mpodkolzin@edu.hse.ru', password='SuperPassword'):
    session = requests.session()
    session.post('https://online.hse.ru/login/index.php',
                 data={'username': email,
                       'password': password})
    return session


def check_send_messages():
    # todo: можно вынести, зачем каждый раз получать?
    next_sem = None
    for n, sem in seminars.items():
        if datetime.now() < sem['171_date']:
            next_sem = sem
            break

    num_days = (next_sem['171_date'].date() - datetime.now().date()).days
    # if num_days > 7:
    #     return

    for u in User.objects(uid__in=sessions.keys()):
        if u.remind_date and datetime.now() >= u.remind_date:
            u.remind_date = datetime.now() + timedelta(minutes=30)
            u.save()

            kb = types.ReplyKeyboardMarkup()
            kb.row('Да', 'Напомни мне через...')
            reply = f'Через {num_days} дней ({next_sem["171_date"].strftime("%d.%m.%Y")}) состоится семинар на тему "{sem["theme"]}", хочешь подготовиться?'
            sent = bot.send_message(u.uid, reply, reply_markup=kb)
            bot.clear_step_handler_by_chat_id(u.uid)
            bot.register_next_step_handler(sent, process_event_step)


def update_seminars():
    """
    Заполняет словарь с расписанием семинаров
    """
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
        if r.th.text != '' and tds[0].text != '':
            seminars[r.th.text] = {
                '171_date': datetime.strptime(tds[0].text, '%d.%m.%y'),
                '172_date': datetime.strptime(tds[1].text, '%d.%m.%y'),
                '173_date': datetime.strptime(tds[2].text, '%d.%m.%y'),
                '174_date': datetime.strptime(tds[3].text, '%d.%m.%y'),
                '175_date': datetime.strptime(tds[4].text, '%d.%m.%y'),
                'theme': tds[5].text,
                'content': tds[6].text,
                'test': tds[7].text
            }


def timer():
    # todo: tick overflow
    tick = 0
    while not stop:
        time.sleep(1)
        tick += 1

        if tick % 5 == 0:
            check_send_messages()
        if tick % (30 * 60) == 0:
            update_seminars()


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
        del sessions[user.uid]
        user.cookies = None
        user.save()
        bot.send_message(user.uid, 'Ты разлогинился', reply_markup=types.ReplyKeyboardRemove())
    else:
        bot.send_message(user.uid, 'Ты не залогинен')


@bot.message_handler(func=is_logged_in)
def logged_in_handler(message):
    user = get_user(message)
    session = sessions[user.uid]
    msg_text = message.text.lower()

    if msg_text == 'страница курса':
        bot.send_message(user.uid, 'https://online.hse.ru/course/view.php?id=1845')

    elif msg_text == 'расписание модуля':
        # todo: Добавить выбор группы
        reply = ''
        for k, v in seminars.items():
            reply += 'Семинар № {}\n"{}"\nДата: {}\nМатериал: {}\nТест: {}\n\n'.format(k, v['theme'], v['171_date'].strftime('%d.%m.%Y'), v['content'], v['test'])

        bot.send_message(user.uid, reply)

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

    else:
        bot.send_message(user.uid, 'Не знаю о чем ты')


@bot.message_handler(func=lambda m: not is_logged_in(m))
def not_logged_in_handler(message):
    user = get_user(message)
    bot.send_message(user.uid, 'Напиши /login, чтобы залогиниться')


def process_email_step(message):
    user = get_user(message)

    user.email = message.text
    user.save()

    bot.send_message(user.uid, 'Введи пароль')
    bot.register_next_step_handler(message, process_password_step)


def process_password_step(message):
    user = get_user(message)

    user.password = message.text
    user.save()

    session = requests.session()
    payload = {'username': user.email, 'password': user.password}
    r = session.post('https://online.hse.ru/login/index.php', data=payload)
    soup = BeautifulSoup(r.text, features='lxml')
    if soup.find(id='loginerrormessage') is not None:
        bot.send_message(user.uid, 'Неверный email или пароль!')
    else:
        soup = BeautifulSoup(session.get('https://online.hse.ru/my/').text, features='lxml')

        user.surname, user.name = soup.find(class_='block_profilefields_fullname').text.split()
        user.cookies = json.dumps(requests.utils.dict_from_cookiejar(session.cookies))
        # todo: chosen_time is reset after relogin
        user.chosen_time = datetime.strptime('9:00', '%H:%M');
        user.save()

        sessions[user.uid] = session

        reply = (f'Привет, {user.name}!\n\n'
                 'Теперь я буду напоминать тебе о наступающих событиях курса "Проектная документация"\n\n'
                 'Чтобы выйти из системы, напиши /logout')
        bot.send_message(user.uid, reply, reply_markup=menu)


def process_event_step(message):
    user = get_user(message)
    msg_text = message.text.lower()

    if msg_text == 'да':
        bot.send_message(user.uid, 'Готовься', reply_markup=menu)

    elif msg_text == 'напомни мне через...':
        kb = types.ReplyKeyboardMarkup()
        kb.row('Через час', 'Через 2 часа', 'Через 4 часа')
        kb.row('Через 8 часов', 'Завтра', 'Через 3 секунды')
        bot.send_message(user.uid, 'Через сколько времени тебе напомнить?', reply_markup=kb)
        bot.register_next_step_handler(message, process_choice_time_step)

    else:
        bot.send_message(user.uid, 'Используй меню')
        bot.register_next_step_handler(message, process_event_step)


# todo: refactor
def process_choice_time_step(message):
    user = get_user(message)
    msg_text = message.text.lower()

    if msg_text == 'через час':
        hours = 1
        reply = 'Хорошо, напомню тебе через час'

    elif msg_text == 'через 2 часa':
        hours = 2
        reply = 'Хорошо, напомню тебе через 2 часа'

    elif msg_text == 'через 4 часa':
        hours = 4
        reply = 'Хорошо, напомню тебе через 4 часа'

    elif msg_text == 'через 8 часов':
        hours = 8
        reply = 'Хорошо, напомню тебе через 8 часов'

    elif msg_text == 'завтра':
        hours = 24
        reply = 'Хорошо, напомню тебе завтра'

    elif msg_text == 'через 3 секунды':
        hours = 3 / 3600
        reply = 'Хорошо, напомню тебе через 3 секунды'

    else:
        bot.send_message(user.uid, 'Используй меню')
        bot.register_next_step_handler(message, process_choice_time_step)
        return

    bot.send_message(user.uid, reply, reply_markup=menu)
    user.remind_date = datetime.now() + timedelta(hours=hours)
    user.save()


def process_settings_step(message):
    user = get_user(message)
    msg_text = message.text.lower()

    if msg_text in ['9:00', '10:00', '11:00', '12:00']:
        reply = f'Хорошо, я буду отправлять тебе уведомление ежедневно в {msg_text}'
        user.chosen_time = datetime.strptime(msg_text, '%H:%M')
        user.save()

    elif msg_text == 'назад':
        reply = 'Время не изменено'

    else:
        bot.send_message(user.uid, 'Используй меню')
        bot.register_next_step_handler(message, process_settings_step)
        return

    bot.send_message(user.uid, reply, reply_markup=menu)


if __name__ == '__main__':
    try:
        load_cookies()
        try:
            bot_session = sessions[list(sessions.keys())[0]]
        except:
            bot_session = get_session()

        update_seminars()
        # seminars['1']['date'] = datetime.now() + timedelta(days=2)
        threading.Thread(target=timer).start()

        print('Start polling...')
        bot.polling()
    finally:
        stop = True
        print('End polling...')
