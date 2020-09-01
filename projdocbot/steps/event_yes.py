from projdocbot import bot, get_user


def process_event_yes_step(message):
    user = get_user(message)
    msg_text = message.text.lower()

    if msg_text == 'начать тест':
        process_test_step(message)

    elif msg_text == 'отменить':
        message.text = 'напомни мне через...'
        process_event_step(message)

    else:
        bot.send_message(user.uid, 'Используй меню')
        bot.register_next_step_handler(message, process_event_yes_step)


from projdocbot.steps.test import process_test_step
from projdocbot.steps.event import process_event_step
