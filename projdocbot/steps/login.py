import json
import requests
from types import SimpleNamespace
from datetime import datetime, timedelta

from telebot import types
from bs4 import BeautifulSoup

from projdocbot import bot, get_user, users, menu
from projdocbot.mongo import User


def process_email_step(message):
    uid = message.from_user.id

    for k, u in users.items():
        if u.email == message.text.lower():
            bot.send_message(uid, 'Пользователь уже залогинен на другом устройстве!')
            return

    users[uid] = SimpleNamespace(email=message.text.lower())

    bot.send_message(uid, 'Введи пароль')
    bot.register_next_step_handler(message, process_password_step)


def process_password_step(message):
    uid = message.from_user.id
    email = users[uid].email
    password = message.text

    session = requests.session()
    payload = {'username': email, 'password': password}
    r = session.post('https://online.hse.ru/login/index.php', data=payload)
    soup = BeautifulSoup(r.text, features='lxml')
    if soup.find(id='loginerrormessage') is not None:
        bot.send_message(uid, 'Неверный email или пароль!')
        del users[uid]
    else:
        soup = BeautifulSoup(session.get('https://online.hse.ru/my/').text, features='lxml')

        users[uid].session = session
        users[uid].question = 0
        users[uid].answers = []

        user = User.objects(email=email).first() or User(email=email)
        user.uid = uid
        user.surname, user.name = soup.find(class_='block_profilefields_fullname').text.split()
        user.cookies = json.dumps(requests.utils.dict_from_cookiejar(session.cookies))
        user.chosen_time = user.chosen_time or datetime.strptime('9:00', '%H:%M')
        user.remind_date = user.remind_date or datetime.now() + timedelta(minutes=5)
        user.group = '1'
        user.save()

        kb = types.ReplyKeyboardMarkup()
        (kb.row('БИВ171'), kb.row('БИВ172'), kb.row('БИВ173'), kb.row('БИВ174'), kb.row('БИВ175'))
        bot.send_message(user.uid, 'Выбери, в какой группе ты учишься', reply_markup=kb)
        bot.register_next_step_handler(message, process_choose_group)


def process_choose_group(message):
    user = get_user(message)
    msg_text = message.text.lower()

    if msg_text not in ['бив171', 'бив172', 'бив173', 'бив174', 'бив175']:
        bot.send_message(user.uid, 'Используй меню')
        bot.register_next_step_handler(message, process_choose_group)
        return

    user.group = msg_text[-1]
    user.save()

    reply = (f'Привет, {user.name}!\n\n'
             'Теперь я буду напоминать тебе о наступающих событиях курса "Проектная документация"\n\n'
             'Чтобы выйти из системы, напиши /logout')
    bot.send_message(user.uid, reply, reply_markup=menu)
