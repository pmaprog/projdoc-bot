from telebot import types

from projdocbot import bot, get_user


def process_event_step(message):
    user = get_user(message)
    msg_text = message.text.lower()

    if msg_text == 'да':
        kb = types.ReplyKeyboardMarkup()
        kb.row('Начать тест', 'Отменить')
        bot.send_message(user.uid, 'Вот ссылка на материал для подготовки. Через 30 минут, я предложу тебе пройти тест, если готов сейчас нажми на "Начать тест"', reply_markup=kb)
        bot.register_next_step_handler(message, process_event_yes_step)

    elif msg_text == 'напомни мне через...':
        kb = types.ReplyKeyboardMarkup()
        kb.row('Через час', 'Через 2 часа', 'Через 4 часа')
        kb.row('Через 8 часов', 'Завтра', 'Через 3 секунды')
        bot.send_message(user.uid, 'Через сколько времени тебе напомнить?', reply_markup=kb)
        bot.register_next_step_handler(message, process_choice_time_step)

    else:
        bot.send_message(user.uid, 'Используй меню')
        bot.register_next_step_handler(message, process_event_step)


from projdocbot.steps.event_yes import process_event_yes_step
from projdocbot.steps.choice_time import process_choice_time_step
