import os
import telebot
from mongo import *
from argparse import ArgumentParser

bot = telebot.TeleBot(os.getenv('PROJDOC_TOKEN'))


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('hour', type=int)
    args = parser.parse_args()
    hour = args.hour

    users = User.objects(when_to_remind=hour)
    for u in users:
        bot.send_message(u.uid, 'настало то время братик')
