import os

import telebot
from telebot import types

from projdocbot.mongo import User

bot = telebot.TeleBot(os.getenv('PROJDOC_TOKEN'))
stop = False
users = {}
seminars = {}
seminars_dates = {}
next_sem = {}
bot_session = None

GROUPS = ('1', '2', '3', '4', '5')

menu = types.ReplyKeyboardMarkup()
menu.row('Страница курса')
menu.row('Расписание модуля')
menu.row('Текущие оценки')
menu.row('Изменить время ежедневного уведомления')

menu.row('DEBUG: сбросить тест')
menu.row('DEBUG: отправить уведомление')
bot.send_message(187471109, 'a', reply_markup=menu)


def get_user(message):
    user = User.objects(uid=message.from_user.id).first()

    if not user:
        user = User(uid=message.from_user.id)
        user.save()

    return user
