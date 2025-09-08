import telebot
from telebot import types
from yoomoney import Client, Quickpay
from datetime import datetime
from random import choice
from string import ascii_uppercase
import sqlite3
import json
from dotenv import load_dotenv
import os

load_dotenv()

#start getting api keys

file = open('price_list.json', 'r')
month_price_data = json.load(file)
file.close()

tok = os.getenv('TG_TOK')
umoney_tok = os.getenv('YOOMONEY_TOK')

#end getting api keys


#start init
client = Client(umoney_tok)
user = client.account_info()
bot = telebot.TeleBot(tok)
#end init

#create list of buttons
def create_a_markup(arr):
    ret = types.InlineKeyboardMarkup()

    for i in arr:
        ret.add(types.InlineKeyboardButton(i[0], callback_data=i[1]))

    return ret



main_text = "<b>Выберите действие</b>"

menu_markup = create_a_markup([
    ("Купить ключ", "buy"),
    ("Мои ключи", "all_keys"),
    ("Помощь", "help")
])

all_keys_markup = create_a_markup([
    ("Меню", "menu")
])



ls_buttons_buy = [("Меню", "menu")]

for i in month_price_data["month"]:
    ls_buttons_buy.append((f"Ключ на {i} мес. ({month_price_data["month"][i]}р)", f"key_{i}_month"))

choose_markup = create_a_markup(ls_buttons_buy)




@bot.message_handler(commands=['start'])
def main_func(message):
    bot.send_message(message.chat.id, main_text, reply_markup=menu_markup, parse_mode='HTML')

    connection = sqlite3.connect('vpn_database.db')
    cursor = connection.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
    id INTEGER AUTO_INCREMENT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    keys TEXT
    )
    ''')

    try:
        cursor.execute(f"INSERT INTO Users (username, keys) VALUES ({bot.get_me().id}, '[]');")
    except Exception as e:
        ...

    connection.commit()
    connection.close()







@bot.message_handler(content_types=['text'])
def message_func(message):
    bot.delete_message(message.chat.id, message.message_id, 100)



def func_buy_key(x_call, x_bot, duration, x_sum):
    rand_part_lable = ''.join(choice(ascii_uppercase) for i in range(12))

    new_label = f"{x_call.message.chat.id}_{datetime.now()}_{rand_part_lable}"
    quickpay = Quickpay(
        receiver="4100119317545987",
        quickpay_form="shop",
        targets=f"VPN {duration} month",
        paymentType="SB",
        sum=x_sum,
        label=new_label
        )

    msg_txt = f'<b>Ключ на {duration} мес.({x_sum}р)</b>\n<a href="{quickpay.redirected_url}">Ссылка на оплату.</a>\n<b>После оплаты нажмите кнопку "Оплачено"</b>'

    link_ret = types.InlineKeyboardMarkup()
    link_ret.add(types.InlineKeyboardButton("Оплачено", callback_data=f"payment|{new_label}"))
    link_ret.add(types.InlineKeyboardButton("Меню", callback_data=f"menu"))

    x_bot.edit_message_text(chat_id=x_call.message.chat.id, message_id=x_call.message.message_id,
                          text=msg_txt,
                          reply_markup=link_ret, parse_mode='HTML')





@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == 'buy':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=main_text, reply_markup=choose_markup, parse_mode='HTML')
    
    if call.data == 'help':
        help_text = "<b>По всем вопросам/проблемам:</b>\n@vsndrg <b>или</b> @mz4ls"
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=help_text, reply_markup=all_keys_markup, parse_mode='HTML')

    if call.data[0:3] == 'key':
        r = call.data.split("_")[1]
        func_buy_key(call, bot, int(r), month_price_data["month"][r])

    if call.data == "menu":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=main_text,
                              reply_markup=menu_markup, parse_mode='HTML')

    if call.data == "all_keys":

        us_id = bot.get_me().id

        connection = sqlite3.connect('vpn_database.db')
        cursor = connection.cursor()

        cursor.execute(f'''
        SELECT keys FROM Users WHERE username="{us_id}";
        ''')
        res = json.loads(cursor.fetchone()[0])

        connection.commit()
        connection.close()



        if len(res) <= 0:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text="<b>У вас пока нет ключей</b>",
                                  reply_markup=all_keys_markup, parse_mode='HTML')
        else:
            txt_to_send = ""
            for m in range(len(res)):
                txt_to_send += f"<em>({res[m][1][0]}.{res[m][1][1]}.{res[m][1][2]}, {res[m][2]} мес.):</em>\n<b>{res[m][0]}</b>\n\n"

            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=txt_to_send,
                                  reply_markup=all_keys_markup, parse_mode="HTML")

    if call.data[0:7] == "payment":
        dt_label = call.data.split("|")[1]

        history = client.operation_history(label=dt_label)

        am = -1
        for operation in history.operations:
            if operation.label == dt_label:
                if operation.status == "success":
                    am = operation.amount
                    break

        #TEMP: am == -1 is just for debug. In prod replace to am != -1
        if am == -1:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=main_text,
                                  reply_markup=menu_markup, parse_mode='HTML')

            #start add key

            us_id = bot.get_me().id

            connection = sqlite3.connect('vpn_database.db')
            cursor = connection.cursor()

            cursor.execute(f'''
            SELECT keys FROM Users WHERE username="{us_id}";
            ''')
            res = json.loads(cursor.fetchone()[0])

            new_gen_key = dt_label #TEMP: here is needed to get real outline key (instead pf dt_label)

            current_data = datetime.now()
            res.append([new_gen_key, [current_data.day, current_data.month, current_data.year], month_price_data["price"]["199"]]) #price_list[200] just for debug

            cursor.execute(f"UPDATE Users SET keys = '{json.dumps(res)}' WHERE username = '{us_id}'")

            connection.commit()
            connection.close()


            #end add key


            bot.send_message(call.message.chat.id, f"<em>Оплата прошла успешно! Ваш ключ:</em>\n<b>{new_gen_key}</b>", parse_mode="HTML")
        else:
            bot.send_message(call.message.chat.id, f"<b>Оплата не прошла, попробуйте снова</b>", parse_mode='HTML')



#while True:
#    try:
#        bot.polling(none_stop=True)
#    except Exception as e:
#        print(f"Polling error: {e}")
#        time.sleep(5)  # Wait before retrying

bot.polling(none_stop=True)
