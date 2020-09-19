from datetime import datetime, timedelta

from projdocbot import bot, get_user, menu


def process_choose_time_step(message):
    user = get_user(message)
    msg_text = message.text.lower()

    if msg_text == 'завтра':
        user.notify_tommorow()
        bot.send_message(user.uid, 'Хорошо, напомню тебе завтра', reply_markup=menu)
        return

    hours = None
    if msg_text == 'через час':
        hours = 1
        reply = 'Хорошо, напомню тебе через час'

    elif msg_text == 'через 2 часа':
        hours = 2
        reply = 'Хорошо, напомню тебе через 2 часа'

    elif msg_text == 'через 4 часа':
        hours = 4
        reply = 'Хорошо, напомню тебе через 4 часа'

    elif msg_text == 'через 8 часов':
        hours = 8
        reply = 'Хорошо, напомню тебе через 8 часов'

    elif msg_text == 'через 3 секунды':
        hours = 3 / 3600
        reply = 'Хорошо, напомню тебе через 3 секунды'

    else:
        bot.send_message(user.uid, 'Используй меню')
        bot.register_next_step_handler(message, process_choose_time_step)
        return

    bot.send_message(user.uid, reply, reply_markup=menu)
    user.notify_dt = datetime.now() + timedelta(hours=hours)
    user.save()
