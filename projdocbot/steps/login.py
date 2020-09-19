import json
import requests
from types import SimpleNamespace
from datetime import datetime, timedelta

from telebot import types
from bs4 import BeautifulSoup

from projdocbot import bot, get_user, sessions, menu, setup_chat_logger
from projdocbot.mongo import User


def process_email_step(message):
    uid = message.from_user.id
    email = message.text.lower()

    for k, u in sessions.items():
        if u.email == email:
            bot.send_message(uid, 'Пользователь уже залогинен на другом аккаунте Telegram!\nПиши @pmaprog если хочешь сменить аккаунт')
            return

    sessions[uid] = SimpleNamespace(email=email, test=None,
                                 question=0, answers=[], url=None,
                                 logger=setup_chat_logger(email, email + '.log'))

    bot.send_message(uid, 'Введи пароль')
    bot.register_next_step_handler(message, process_password_step)


def process_password_step(message):
    uid = message.from_user.id
    email = sessions[uid].email
    password = message.text

    session = requests.session()
    payload = {'username': email, 'password': password}
    r = session.post('https://online.hse.ru/login/index.php', data=payload)
    soup = BeautifulSoup(r.text, features='lxml')
    if soup.find(id='loginerrormessage') is not None:
        bot.send_message(uid, 'Неверный email или пароль!')
        del sessions[uid]
    else:
        soup = BeautifulSoup(session.get('https://online.hse.ru/my/').text, features='lxml')

        sessions[uid].session = session

        user = User.objects(email=email).first() or User(email=email)
        user.uid = uid
        user.surname, user.name = soup.find(class_='block_profilefields_fullname').text.split()
        user.cookies = json.dumps(requests.utils.dict_from_cookiejar(session.cookies))
        user.chosen_time = user.chosen_time or datetime.strptime('9:00', '%H:%M')
        user.group = '1'
        user.save()

        kb = types.ReplyKeyboardMarkup()
        (kb.row('БИВ171'), kb.row('БИВ172'), kb.row('БИВ173'), kb.row('БИВ174'), kb.row('БИВ175'))
        bot.send_message(user.uid, 'Выбери, в какой группе ты учишься', reply_markup=kb)
        bot.register_next_step_handler(message, process_choose_group_step)


def process_choose_group_step(message):
    user = get_user(message)
    msg_text = message.text.lower()

    if msg_text not in ['бив171', 'бив172', 'бив173', 'бив174', 'бив175']:
        bot.send_message(user.uid, 'Используй меню')
        bot.register_next_step_handler(message, process_choose_group_step)
        return

    user.group = msg_text[-1]
    user.notify_dt = user.notify_dt or datetime.now() + timedelta(minutes=5)
    user.save()

    reply = (f'Привет, {user.name}!\n\n'
             'Теперь я буду напоминать тебе о подготовке к предстоящим семинарам курса "Проектная документация"')
    bot.send_message(user.uid, reply, reply_markup=menu)
