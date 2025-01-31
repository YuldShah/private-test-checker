import os.path
import telebot
from telebot import types
from db_manager import *
from answers import *
import xlsxwriter

API_TOKEN = os.getenv('API_TOKEN', '')
ADMINS = list(os.getenv('ADMINS', '').split(','))
number_of_tests = len(answers_for_test)
tests = [str(i) for i in range(1, number_of_tests + 1)]
bot = telebot.TeleBot(API_TOKEN)
answers = {}



# def find_user_id_of_token(message):
#     bot.send_message(message.chat.id, "Tokenni kiriting:")
#     set_user_state(message.from_user.id, 'find')

@bot.message_handler(commands=['find'])
def return_user_id(message):
    try:
        user_token = message.text.split()[1]
    except IndexError:
        bot.send_message(message.chat.id, "Iltimos, to'g'ri formatda token kiriting: /find <token>")
        return
    user_id = get_user_id(user_token)
    if user_id is not None:
        bot.send_message(message.chat.id, f"User ID: {user_id}")
    else:
        bot.send_message(message.chat.id, "Token topilmadi.")
    set_user_state(message.from_user.id, '')

@bot.message_handler(commands=['token'])
def generate_tokens_command(message):
    print(f"{ADMINS}")
    if str(message.from_user.id) in ADMINS:
        try:
            num_tokens = int(message.text.split()[1])
            tokens = generate_tokens(num_tokens)
            # tokens = get_user_tokens()
            token_list = "\n".join([token for token in tokens])
            with open("tokens.txt", "w") as file:
                file.write(token_list)
            with open("tokens.txt", "rb") as file:
                bot.send_document(message.chat.id, file)
        except (IndexError, ValueError):
            bot.send_message(message.chat.id, "Iltimos, to'g'ri formatda raqam kiriting: /token <soni>")
    else:
        bot.send_message(message.chat.id, "Sizda bu buyruqni bajarish uchun ruxsat yo'q.")

@bot.message_handler(commands=['getall'])
def get_all_tokens_command(message):
    if str(message.from_user.id) in ADMINS:
        tokens = get_user_tokens()
        token_list = "\n".join([token[1] for token in tokens])
        with open("all_tokens.txt", "w") as file:
            file.write(token_list)
        with open("all_tokens.txt", "rb") as file:
            bot.send_document(message.chat.id, file)
    else:
        bot.send_message(message.chat.id, "Sizda bu buyruqni bajarish uchun ruxsat yo'q.")

@bot.message_handler(commands=['results'])
def get_results_command(message):
    if str(message.from_user.id) in ADMINS:
        results = get_user_results()
        workbook = xlsxwriter.Workbook('results.xlsx')
        worksheet = workbook.add_worksheet()
        
        # Write headers
        headers = ['User ID', 'Telegram ID', 'Test', 'Score', 'Datetime']
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header)
        
        # Write data
        for row_num, row_data in enumerate(results, start=1):
            worksheet.write(row_num, 0, row_data[0])  # User ID
            worksheet.write(row_num, 1, row_data[1])  # Telegram ID
            worksheet.write(row_num, 2, row_data[2])  # Test
            worksheet.write(row_num, 3, row_data[3])  # Score
            worksheet.write(row_num, 4, row_data[4])  # Datetime
        
        workbook.close()
        
        with open('results.xlsx', 'rb') as file:
            bot.send_document(message.chat.id, file)
    else:
        bot.send_message(message.chat.id, "Sizda bu buyruqni bajarish uchun ruxsat yo'q.")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Token kalitingizni kiriting (Token kalit olmagan bo'lsangiz @satelbekadmin):")
    set_user_state(message.from_user.id, 'login')

@bot.message_handler(commands=['help'])
def send_welcome(message):
    if str(message.chat.id) in ADMINS:
        bot.send_message(message.chat.id, "/start - Start submitting your answers\n\n/token <number> - Generate <number> of tokens and get newly generated tokens\n\n/find <token> - Get User ID\n\n/getall - Get all tokens\n\n/results - Get all results")
    else:
        bot.send_message(message.chat.id, "/start - Testlarga javoblarini yuborishni boshlash")

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
        add_result(user_id, callback.message.chat.id, topic, score)
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = [types.InlineKeyboardButton(text=item, callback_data=item) for item in tests]
        markup.add(*buttons)
        bot.send_message(callback.message.chat.id, "Mavzuni tanlang:", reply_markup=markup)
    elif dots == 0:
        topic = callback.data
        if os.path.exists(f'tests/{topic}.pdf'):
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
            with open(f'tests/{topic}.pdf', 'rb') as file:
                if topic!=2:
                    bot.send_document(callback.message.chat.id, file)
                else:
                    bot.send_document(callback.message.chat.id, file, caption="⚠️ Hammaning diqqatiga 6- va 9- savollarga C javobini belgilaveringlar togri hisoblaymiz.\n26 va 29- savolga A qilib belgilaysizlar\n11-savolda tepada darajada 8 turibdi  yoki B Javob qilinsa togri Deb hisoblaymiz\n30-savol bunisini emas\nNarigi betdagini javobini yuklaysizlar\nOzgina muammo bolibdi uzr.")
            bot.send_message(callback.message.chat.id, f"{topic} testning savolini tanlang:", reply_markup=markup)
        else:
            bot.send_message(callback.message.chat.id, f"Test hozircha yopiq.")
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
    bot.delete_webhook(drop_pending_updates=True)
    bot.polling(none_stop=True)
