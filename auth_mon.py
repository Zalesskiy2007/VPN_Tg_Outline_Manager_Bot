import telebot
from telebot import types
import time
from yoomoney import Client, Quickpay
from datetime import datetime
from random import choice
from string import ascii_uppercase
import sqlite3

file = open("tmp_token_save.txt", "r")
tok = file.read()
file.close()

file = open("tmp_umoney_save.txt", "r")
umoney_tok = file.read()
file.close()

client = Client(umoney_tok)
user = client.account_info()




bot = telebot.TeleBot(tok)


def create_a_markup(arr):
    ret = types.InlineKeyboardMarkup()

    for i in arr:
        ret.add(types.InlineKeyboardButton(i[0], callback_data=i[1]))

    return ret


main_text = "Выберите действие"

menu_markup = create_a_markup([
    ("Купить ключ", "buy"),
    ("Мои ключи", "all_keys")
])

all_keys_markup = create_a_markup([
    ("Меню", "menu")
])




choose_markup = create_a_markup([
    ("Меню", "menu"),
    ("Ключ на 1 месяц (200р)", "buy_1_month"),
    ("Ключ на 3 месяца (350р)", "buy_3_month"),
    ("Ключ на 6 месяцев (650р)", "buy_6_month")
])



@bot.message_handler(commands=['start'])
def main_func(message):
    bot.send_message(message.chat.id, main_text, reply_markup=menu_markup)

    connection = sqlite3.connect('my_database.db')
    cursor = connection.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
    id INTEGER AUTO_INCREMENT PRIMARY KEY,
    username TEXT NOT NULL,
    keys TEXT[]
    )
    ''')

    connection.commit()
    connection.close()

    #user = bot.get_me()
    #bot.send_message(message.chat.id, user.id)



@bot.message_handler(content_types=['text'])
def message_func(message):
    bot.delete_message(message.chat.id, message.message_id, 100)



def func_buy_key(x_call, x_bot, duration, x_sum):
    rand_part_lable = ''.join(choice(ascii_uppercase) for i in range(12))

    new_label = f"{x_call.message.chat.id}_{datetime.now()}_{rand_part_lable}"
    quickpay = Quickpay(
        receiver="4100119303227519",
        quickpay_form="shop",
        targets=f"VPN {duration} month",
        paymentType="SB",
        sum=x_sum,
        label=new_label
        )

    msg_id_url = x_bot.send_message(x_call.message.chat.id, quickpay.redirected_url)

    start_time = time.time()
    end_time = time.time()
    flag = False

    while(end_time - start_time <= 10):
        history = client.operation_history(label=new_label)

        for operation in history.operations:
            if operation.label == new_label:
                if operation.status == "success":
                    flag = True
                    break
        end_time = time.time()

    if flag == False:
        x_bot.send_message(x_call.message.chat.id, "Время на оплату истекло, покупка отменена :(")
    else:
        outline_key = "empty"
        #get_a_outline_key
        #put_key_in_database
        x_bot.send_message(x_call.message.chat.id, f"Оплата произошла успешло!\nВаш ключ: {outline_key}")
    x_bot.send_message(x_call.message.chat.id, main_text, reply_markup=menu_markup)


def func_get_all_key(x_call, x_bot):
    return 0


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == 'buy':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=main_text, reply_markup=choose_markup)

    if call.data == 'buy_1_month':
        func_buy_key(call, bot, 1, 200)
    if call.data == 'buy_3_month':
        func_buy_key(call, bot, 3, 350)
    if call.data == 'buy_6_month':
        func_buy_key(call, bot, 6, 650)


    if call.data == "menu":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=main_text,
                              reply_markup=menu_markup)

    if call.data == "all_keys":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="У вас пока нет ключей",
                              reply_markup=all_keys_markup)




#while True:
#    try:
#        bot.polling(none_stop=True)
#    except Exception as e:
#        print(f"Polling error: {e}")
#        time.sleep(5)  # Wait before retrying

bot.polling(none_stop=True)
