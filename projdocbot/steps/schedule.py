from projdocbot import bot, get_user, seminars, seminars_dates, menu


def process_schedule_step(message):
    user = get_user(message)
    msg_text = message.text.lower()

    if msg_text in ['бив171', 'бив172', 'бив173', 'бив174', 'бив175']:
        group = msg_text[-1]
        reply = ''
        for k, v in seminars.items():
            # reply += 'Семинар № {}\n"{}"\nДата: {}\nМатериал: {}\n\n'.format(
            #     k, v['theme'], seminars_dates[k][group].strftime('%d.%m.%Y'), v['content']
            # )

            reply += 'Семинар № {}\n"{}"\nДата: {}\n\n'.format(
                k, v.theme, seminars_dates[k][group].strftime('%d.%m.%Y')
            )

        bot.send_message(user.uid, reply, reply_markup=menu)
    elif msg_text == 'назад':
        bot.send_message(user.uid, 'Возращаемся в меню', reply_markup=menu)
    else:
        bot.send_message(user.uid, 'Используй меню')
        bot.register_next_step_handler(message, process_schedule_step)
