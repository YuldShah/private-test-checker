import os.path
from flask import Flask, request, redirect, url_for
import telebot
from telebot import types
from db_manager import *
from answers import *

API_TOKEN = ''
number_of_tests = len(answers_for_test)
tests = [str(i) for i in range(1, number_of_tests + 1)]
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)
answers = {}


@app.route('/', methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return '!', 200


@app.route('/results')
def getResults():
    return get_user_results()


@app.route('/tokens')
def getTokens():
    return get_user_tokens()


@app.route('/generate_tokens/<int:n>')
def generateTokens(n):
    generate_tokens(n)
    return redirect(url_for('getTokens'))


@app.route('/add_tokens/<int:last>/<int:n>')
def addTokens(last, n):
    add_tokens(last, n)
    return redirect(url_for('getTokens'))


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Token kalitingizni kiriting (Token kalit olmagan bo'lsangiz @satelbekadmin):")
    set_user_state(message.from_user.id, 'login')


@bot.message_handler(func=lambda message: get_user_state(message.from_user.id) == 'login', content_types=['text'])
def token_handler(message):
    user_token = message.text
    user_id = get_user_id(user_token)
    if user_id is not None:
        bot.send_message(message.chat.id, "Token qabul qilindi.")
        set_user_state(message.from_user.id, 'user')
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = [types.InlineKeyboardButton(text=item, callback_data=item) for item in tests]
        markup.add(*buttons)
        bot.send_message(message.chat.id, "Mavzuni tanlang:", reply_markup=markup)
        setup_user_session(message.from_user.id, user_id)
    else:
        bot.send_message(message.chat.id, "Token qabul qilinmadi. Token kiriting:")


@bot.callback_query_handler(func=lambda callback: True)
def test_selection_callback_handler(callback):
    dots = callback.data.count('.')
    if '-' in callback.data:
        topic = callback.data.split('-')[1]
        score = 0
        definition = ''
        if answers.get(f'{callback.message.chat.id}.{topic}') is not None:
            for i in sorted(answers[f'{callback.message.chat.id}.{topic}'].keys()):
                if answers_for_test[int(topic) - 1][int(i) - 1] == answers[f'{callback.message.chat.id}.{topic}'][i]:
                    definition += f'{i}. 🟢\n'
                    score += 1
                else:
                    definition += f'{i}. 🔴\n'
            del answers[f'{callback.message.chat.id}.{topic}']
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        bot.send_message(callback.message.chat.id, f'{definition}*{topic} testning natijasi: {score} / {len(answers_for_test[int(topic) - 1])}*', parse_mode='Markdown')
        user_id = get_user_session_info(callback.message.chat.id)
        add_result(user_id, topic, score)
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = [types.InlineKeyboardButton(text=item, callback_data=item) for item in tests]
        markup.add(*buttons)
        bot.send_message(callback.message.chat.id, "Mavzuni tanlang:", reply_markup=markup)
    elif dots == 0:
        topic = callback.data
        markup = types.InlineKeyboardMarkup(row_width=3)
        buttons = []
        for item in range(1, len(answers_for_test[int(topic) - 1]) + 1):
            char = f"🔴 {item}"
            if answers.get(f'{callback.message.chat.id}.{topic}', {}).get(f'{item}') is not None:
                char = f"🟢 {item}"
            buttons.append(types.InlineKeyboardButton(text=char, callback_data=f"{topic}.{item}"))
        markup.add(*buttons)
        markup.add(types.InlineKeyboardButton(text="Testni tugatish", callback_data=f"submit-{topic}"))
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        if os.path.exists(f'tests/{topic}.pdf'):
            with open(f'tests/{topic}.pdf', 'rb') as file:
                bot.send_document(callback.message.chat.id, file)
        bot.send_message(callback.message.chat.id, f"{topic} testning savolini tanlang:", reply_markup=markup)
    elif dots == 1:
        topic, test = callback.data.split('.')
        markup = types.InlineKeyboardMarkup(row_width=4)
        buttons = []
        for item in ['A', 'B', 'C', 'D']:
            char = f"🔴 {item}"
            answer_of_test = answers.get(f'{callback.message.chat.id}.{topic}', {}).get(f'{test}')
            if answer_of_test is not None and answer_of_test == item:
                char = f"🟢 {item}"
            buttons.append(types.InlineKeyboardButton(text=char, callback_data=f"{topic}.{test}.{item}"))
        markup.add(*buttons)
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        bot.send_message(callback.message.chat.id, f"{topic} testning {test} savolini javobni tanlang:", reply_markup=markup)
    elif dots == 2:
        topic, test, answer = callback.data.split('.')
        if f'{callback.message.chat.id}.{topic}' not in answers:
            answers[f'{callback.message.chat.id}.{topic}'] = {}
        answers[f'{callback.message.chat.id}.{topic}'][f'{test}'] = answer
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        markup = types.InlineKeyboardMarkup(row_width=3)
        buttons = []
        for item in range(1, len(answers_for_test[int(topic) - 1]) + 1):
            char = f"🔴 {item}"
            if answers.get(f'{callback.message.chat.id}.{topic}', {}).get(f'{item}') is not None:
                char = f"🟢 {item}"
            buttons.append(types.InlineKeyboardButton(text=char, callback_data=f"{topic}.{item}"))
        markup.add(*buttons)
        markup.add(types.InlineKeyboardButton(text="Testni tugatish", callback_data=f"submit-{topic}"))
        bot.send_message(callback.message.chat.id, f"{topic} testning savolini tanlang:", reply_markup=markup)


if __name__ == "__main__":
    init_db()
    bot.remove_webhook()
    bot.set_webhook(url='/')
    app.run()
