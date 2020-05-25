import os
import random

import dotenv
import redis
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, RegexHandler

import telebot
import re
from telebot import types
import quiz_tools

dotenv.load_dotenv()
QUESTIONS = quiz_tools.get_dict_of_questions()
DB = redis.Redis(host=os.environ['HOST'],
                 password=os.environ['PASSWORD_REDIS'],
                 port=os.environ['PORT'],
                 decode_responses=True, db=0
                 )


def main():
    token_tg = os.environ["TOKEN_TG"]
    run_tg_bot(token_tg)


def handle_new_question_request(bot, update):
    question = random.choice(list(QUESTIONS.keys()))
    update.message.reply_text(f'Вопрос: {question}')
    DB.set(update.message.chat_id, question)


def handle_give_up(bot, update):
    question = DB.get(update.message.chat_id)
    answer = QUESTIONS[question]
    update.message.reply_text(f'Ответ: {answer}', reply_markup=get_keyboard())


def handle_solution_attempt(bot, update):
    question = DB.get(update.message.chat_id)
    text = update.message.text
    if QUESTIONS[question] == text:
        update.message.reply_text('Правильно!')
    else:
        update.message.reply_text('Неправильно! Попробуйте еще раз', reply_markup=get_keyboard())


def get_keyboard():
    custom_keyboard = types.InlineKeyboardMarkup()
    custom_keyboard.add(types.InlineKeyboardMarkup(text='Новый вопрос', callback_data='Новый вопрос'))
    custom_keyboard.add(types.InlineKeyboardMarkup(text='Сдаться', callback_data='Сдаться'))
    return custom_keyboard

# kb = types.InlineKeyboardMarkup()
#     # Добавляем колбэк-кнопку с содержимым "test"
#     kb.add(types.InlineKeyboardButton(text="Нажми меня", callback_data="test"))
#     results = []
#     single_msg = types.InlineQueryResultArticle(
#         id="1", title="Press me",
#         input_message_content=types.InputTextMessageContent(message_text="Я – сообщение из инлайн-режима"),
#         reply_markup=kb
#     )
#     results.append(single_msg)
#     bot.answer_inline_query(query.id, results)


def run_tg_bot(token_tg):
    updater = Updater(token_tg)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start),
                      RegexHandler('Новый вопрос', handle_new_question_request),
                      RegexHandler('Сдаться', handle_give_up),
                      MessageHandler(Filters.text, handle_solution_attempt)
                      ],
        states={},
        fallbacks=[]
    )

    dispatcher.add_handler(conversation_handler)
    updater.start_polling()

    updater.idle()


def start(bot, update):
    update.message.reply_text('Привет! Я бот для викторин', reply_markup=get_keyboard())


if __name__ == '__main__':
    main()
