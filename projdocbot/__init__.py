import os
import logging

import telebot
from telebot import types, apihelper

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from projdocbot.mongo import User

apihelper.ENABLE_MIDDLEWARE = True

GROUPS = ('1', '2', '3', '4', '5')

bot = telebot.TeleBot(os.getenv('PROJDOC_TOKEN'))
bot.enable_save_next_step_handlers(delay=2)

stop = False
sessions = {}
tests = {}
seminars = {}
seminars_dates = {}
next_sem_num = {}

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/spreadsheets',
         'https://www.googleapis.com/auth/drive.file',
         'https://www.googleapis.com/auth/drive']

creds = ServiceAccountCredentials.from_json_keyfile_name('c:/code/projdoc-bot-creds.json', scope)

gc = gspread.authorize(creds)
sh = gc.open_by_key('10aUd7H3g4GIywgKyIjPVjbUqXCKQEKIiMHhYTSOazi0')

menu = types.ReplyKeyboardMarkup()
menu.row('Страница курса')
menu.row('Расписание')
menu.row('Текущие оценки')
menu.row('Изменить время ежедневного уведомления')


menu.row('DEBUG: сбросить тест')
menu.row('DEBUG: отправить уведомление')
bot.send_message(187471109, 'a', reply_markup=menu)


def setup_chat_logger(name, log_file, level=logging.INFO):
    formatter = logging.Formatter('%(asctime)s;%(levelname)s;%(sem_num)s;"%(message)s"')

    handler = logging.FileHandler('logs/' + log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


def get_user(message):
    return User.objects(uid=message.from_user.id).first()
