import time
from types import SimpleNamespace
from datetime import datetime, timedelta

from telebot import types

import projdocbot
from projdocbot import (bot, sessions, next_sem_num, seminars, seminars_dates, sh,
                        GROUPS)
from projdocbot.steps.event import process_event_step
from projdocbot.steps.test import start_test, stop_test
from projdocbot.mongo import User, UserStatistics


# todo: refactor
def remind_about_seminar(group):
    sem_num = next_sem_num[group]
    sem = seminars[sem_num]
    sem_date = seminars_dates[sem_num][group]

    remained = (sem_date.date() - datetime.now().date()).days
    if remained > 7:
        return

    # filter_ = {f'seminars__{group}__success_date__not__exists': True}
    for u in User.objects(uid__in=sessions.keys(), group=group,
                          notify_dt__lte=datetime.now()):
        if sem_num not in u.seminars:
            u.seminars[sem_num] = UserStatistics()
        if u.seminars[sem_num].success_date is None:
            u.notify_dt = datetime.now() + timedelta(minutes=30)
            u.seminars[sem_num].notifications_count += 1
            u.save()

            kb = types.ReplyKeyboardMarkup()
            kb.row('Да', 'Напомни мне через...')
            reply = f'Через {remained} дней ({sem_date.strftime("%d.%m.%Y")}) состоится семинар на тему\n\n"{sem.theme}",\n\n'
            if len(u.seminars[sem_num].correct_answers_lst) > 0:
                reply += 'в прошлый раз ты не сдал тест, хочешь повторить попытку?'
            else:
                reply += 'хочешь подготовиться и пройти тест?'
            sent = bot.send_message(u.uid, reply, reply_markup=kb)
            bot.clear_step_handler_by_chat_id(u.uid)
            bot.register_next_step_handler(sent, process_event_step)
        else:
            u.notify_tommorow()


def update_seminars():
    """
    Заполняет словарь с расписанием семинаров и словарь с их датами
    """

    rows = sh.worksheet('Расписание').get_all_values()
    for cols in rows[1:]:
        sem_num = cols[0]
        seminars[sem_num] = SimpleNamespace(
            theme=cols[6],
            content=cols[7]
        )
        seminars_dates[sem_num] = {
            '1': datetime.strptime(cols[1], '%d.%m.%Y'),
            '2': datetime.strptime(cols[2], '%d.%m.%Y'),
            '3': datetime.strptime(cols[3], '%d.%m.%Y'),
            '4': datetime.strptime(cols[4], '%d.%m.%Y'),
            '5': datetime.strptime(cols[5], '%d.%m.%Y')
        }

    for g in GROUPS:
        upcoming_seminars = dict(filter(lambda x: x[1][g] >= datetime.now(), seminars_dates.items()))
        new_next_sem_num = min(upcoming_seminars.keys())
        # если следующий семинар сменился, меняем время напоминания на завтрашний день
        if g in next_sem_num and new_next_sem_num != next_sem_num[g]:
            for u in User.objects(group=g):
                u.notify_dt = datetime.now().replace(hour=u.chosen_time.hour,
                                                     minute=u.chosen_time.minute,
                                                     second=0, microsecond=0)
                u.save()

        next_sem_num[g] = new_next_sem_num


def timer():
    tick = 0
    print('Timer started')
    while not projdocbot.stop:
        time.sleep(1)
        tick += 1

        if tick % 5 == 0:
            for g in GROUPS:
                remind_about_seminar(g)

            for u in User.objects(start_test_dt__lte=datetime.now()):
                start_test(u)

            for u in User.objects(stop_test_dt__lte=datetime.now()):
                stop_test(u)
        elif tick % (30 * 60) == 0:
            update_seminars()
            tick = 0  # нужно обнулять, а то будет переполнение
    print('Timer stopped')
