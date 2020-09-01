import json
import requests
from types import SimpleNamespace
from datetime import datetime, timedelta

from bs4 import BeautifulSoup

from projdocbot import bot, get_user, users, menu


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
        user.chosen_time = user.chosen_time or datetime.strptime('9:00', '%H:%M')
        user.remind_date = datetime.now() + timedelta(minutes=5)
        user.save()

        users[user.uid] = SimpleNamespace(
            session=session,
            question=None,
            answers=[]
        )

        reply = (f'Привет, {user.name}!\n\n'
                 'Теперь я буду напоминать тебе о наступающих событиях курса "Проектная документация"\n\n'
                 'Чтобы выйти из системы, напиши /logout')
        bot.send_message(user.uid, reply, reply_markup=menu)
