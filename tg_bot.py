import telebot
import toml
import os
import re
import sqlite3
from requests import ReadTimeout

try:
    config = toml.load('config.toml').get('tg')
    bot_token = config.get('tg_token')
    admin_chat = config.get('admin_chat')
except FileNotFoundError:
    import sys

    sys.exit(-1)

path = f'{os.path.abspath(os.curdir)}/'

bot = telebot.TeleBot(token=bot_token)


# Telegram bots have a limit of 4096 symbols per message, but I don't think this should cause any problems here,
# thus standard bot.send_message(chat_id, text, **kwargs) will do.


def add_escape_chars(input_str) -> str:
    """
    Copied from telebot.formatiing.escape_markdown
    """
    parse = re.sub(r"([_*\[\]()~`>\#\+\-=|\.!\{\}])", r"\\\1", input_str)
    reparse = re.sub(r"\\\\([_*\[\]()~`>\#\+\-=|\.!\{\}])", r"\1", parse)
    return reparse


@bot.message_handler(commands=['help'])
def get_help_message(message):
    bot.send_message(message.chat.id, 'Will add additional info here later.')


@bot.message_handler(commands=['start'])
def send_welcome(message):
    _token = str(message.text)
    if _token and _token != '/start':  # if '/start' command contains an auth code
        # received token
        _token = _token.split()[-1]  # '/start tokenstr' -> tokenstr
        with sqlite3.connect(f"{path}tg/jobs.db") as con:
            cur = con.cursor()
            cur.execute("SELECT user_filename FROM jobs WHERE job_token=?", (_token,))
            filename = cur.fetchone()

            if filename:
                cur.execute("UPDATE jobs SET job_confirmed=1, user_id=? WHERE job_token=?", (message.chat.id, _token,))
                con.commit()
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


def send_notification(user_id, filename, job_token):
    bot.send_message(user_id,
                     f'Calculations on {add_escape_chars(filename)} are complete\!'
                     f'\nYou can now check the results by following the '
                     f'[link](http://127.0.0.1:8070/?token={job_token})',
                     parse_mode='MarkdownV2')

    return 0


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
    except ReadTimeout:
        pass
    except ConnectionError:
        pass
    except Exception as e:
        bot.send_message(admin_chat, f'Ошибка телеграм-бота: {str(e)}')
    finally:
        main(after_crash=True)  # не в except, т.к. send_message тоже может вызвать exception


def launch_bot():
    main()


if __name__ == "__main__":
    main()
