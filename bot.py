import os
import json
import requests
from bs4 import BeautifulSoup
from mongo import User

import telebot
from telebot import types


bot = telebot.TeleBot(os.getenv('PROJDOC_TOKEN'))
sessions = {}

kb = types.ReplyKeyboardMarkup()
kb.row('Страница курса')
kb.row('Расписание модуля')
kb.row('Текущие оценки')


def get_user(message):
    user = User.objects(uid=message.from_user.id).first()

    if not user:
        user = User(uid=message.from_user.id)
        user.save()

    return user


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
        user.save()

        sessions[user.uid] = session

        reply = (f'Привет, {user.name}!\n\n'
                 'Теперь я буду напоминать тебе о наступающих событиях курса "Проектная документация"\n\n'
                 'Чтобы выйти из системы, напиши /logout')
        bot.send_message(user.uid, reply, reply_markup=kb)


def is_logged_in(m):
    user = get_user(m)
    return user and user.uid in sessions


@bot.message_handler(func=is_logged_in)
def logged_in_handler(message):
    user = get_user(message)
    session = sessions[user.uid]

    msg_text = message.text.lower()
    if msg_text == 'страница курса':
        bot.send_message(user.uid, 'https://online.hse.ru/course/view.php?id=1845')

        calendar = session.get('https://online.hse.ru/calendar/view.php?view=month&time=1585688400&course=1845')
        soup = BeautifulSoup(calendar.text, features='lxml')
        lst = soup.find_all(lambda x: x.has_attr('data-event-id'))
        msg = ''
        for i in lst:
            msg += i['title'] + '\n'
        bot.send_message(user.uid, msg)
    elif msg_text == 'расписание модуля':
        bot.send_message(user.uid, 'https://online.hse.ru/mod/page/view.php?id=123827')
    elif msg_text == 'текущие оценки':
        bot.send_message(user.uid, 'https://online.hse.ru/grade/report/user/index.php?id=1845')
    else:
        bot.send_message(user.uid, 'Не знаю о чем ты')


@bot.message_handler(func=lambda m: not is_logged_in(m))
def not_logged_in_handler(message):
    user = get_user(message)
    bot.send_message(user.uid, 'Напиши /login, чтобы залогиниться')


def load_cookies():
    for u in User.objects:
        if u.cookies is not None:
            sessions[u.uid] = requests.session()
            cookies = requests.utils.cookiejar_from_dict(json.loads(u.cookies))
            sessions[u.uid].cookies.update(cookies)


if __name__ == '__main__':
    load_cookies()
    bot.polling()
