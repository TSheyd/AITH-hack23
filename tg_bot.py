import telebot
import toml
import logging
import sqlite3

try:
    config = toml.load('config.toml').get('tg')
    bot_token = config.get('tg_token')
    admin_chat = config.get('admin_chat')
except FileNotFoundError:
    import sys
    sys.exit(-1)


bot = telebot.TeleBot(token=bot_token)
# Telegram bots have a limit of 4096 symbols per message, but I don't think this should cause any problems here,
# thus standard bot.send_message(chat_id, text, **kwargs) will do.


@bot.message_handler(commands=['help'])
def get_help_message(message):
    bot.send_message(message.chat.id, 'Will add additional info here later.')


@bot.message_handler(commands=['start'])
def send_welcome(message):
    _token = str(message.text)
    if _token and _token != '/start':  # if '/start' command contains an auth code
        # received token
        with sqlite3.connect("tg/jobs.db") as con:
            cur = con.cursor()
            cur.execute("SELECT filename FROM jobs WHERE job_token=?", (_token,))
            filename = cur.fetchone()

            if filename:
                bot.send_message(message.chat.id, f'{filename[0]} was added to job queue.\nYou will receive '
                                                  f'a notification when the calculations are finished.')
            else:
                bot.send_message(message.chat.id, f'Oops! Something went wrong during user authentication.'
                                                  f'\nPlease try again by returning to the website.')

    else:  # just a /start command
        bot.send_message(message.chat.id, f'Hi! This bot helps you track jobs at the Koshmarkers website.'
                                          f'\nTo add a job, go to the [website](TODO ADD LINK and md format) '
                                          f'and send your RNAseq data in .tsv or .csv.'
                                          f'\n\nYou can learn more about this tool by clicking [here](TODO) '
                                          f'or by using the /help command (TODO).')


def main(after_crash=False):
    """
    bot.polling() wrapper for error notifications
    :param bool after_crash:
    :return:
    """
    try:
        text_addition = '' if not after_crash else ' после ошибки.'  # сообщение об ошибке может быть и не доставлено
        bot.send_message(admin_chat, f'Бот активирован{text_addition}')
        bot.polling(non_stop=True)
    except Exception as e:
        bot.send_message(admin_chat, f'Ошибка телеграм-бота: {str(e)}')
    finally:
        main(after_crash=True)  # не в except, т.к. send_message тоже может вызвать exception


if __name__ == "__main__":
    main()
