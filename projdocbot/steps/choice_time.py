from datetime import datetime, timedelta

from projdocbot import bot, get_user, menu


# todo: refactor
def process_choice_time_step(message):
    user = get_user(message)
    msg_text = message.text.lower()

    if msg_text == 'завтра':
        tommorow = datetime.now() + timedelta(days=1)
        user.remind_date = tommorow.replace(hour=user.chosen_time.hour,
                                            minute=user.chosen_time.minute,
                                            second=0, microsecond=0)
        user.save()
        bot.send_message(user.uid, 'Хорошо, напомню тебе завтра', reply_markup=menu)
        return

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
