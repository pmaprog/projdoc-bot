from datetime import datetime

from projdocbot import bot, get_user, menu


def process_settings_step(message):
    user = get_user(message)
    msg_text = message.text.lower()

    if msg_text in ['9:00', '10:00', '11:00', '12:00']:
        reply = f'Хорошо, я буду отправлять тебе уведомление ежедневно в {msg_text}'
        user.chosen_time = datetime.strptime(msg_text, '%H:%M')
        user.save()

    elif msg_text == 'назад':
        reply = 'Время не изменено'

    else:
        bot.send_message(user.uid, 'Используй меню')
        bot.register_next_step_handler(message, process_settings_step)
        return

    bot.send_message(user.uid, reply, reply_markup=menu)
