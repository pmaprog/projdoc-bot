from datetime import datetime

from projdocbot import bot, get_user, sessions


def process_event_yes_step(message):
    user = get_user(message)

    remaining_time = user.start_test_dt - datetime.now()
    m, s = int(remaining_time.seconds / 60), remaining_time.seconds % 60

    bot.send_message(user.uid,
                     'Вот ссылка на материал для подготовки:'
                     f'\n\n{sessions[user.uid].url}\n\n'
                     f'Готовься, тест начнется через {m}:{s:02d}')
    bot.register_next_step_handler(message, process_event_yes_step)
