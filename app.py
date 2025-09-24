import telebot
from telebot import types
import requests
import os
from flask import Flask, request
from datetime import datetime

BOT_TOKEN = "1026169981:AAHsIY7oMQ6hbeZlOEkb7ueN7U9SiTtOQMs"
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

TOP_COINS = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    'SOL': 'solana',
    'BNB': 'binancecoin',
    'USDT': 'tether',
    'ADA': 'cardano',
    'DOGE': 'dogecoin',
    'TRX': 'tron',
    'TON': 'toncoin',
    'XRP': 'ripple'
}

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN)
bot.remove_webhook()

def get_coin_price(coin_id, symbol):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd,rub&include_24hr_change=true"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()[coin_id]
            price_usd = data['usd']
            price_rub = data['rub']
            change_24h = data['usd_24h_change']
            change_emoji = "📈" if change_24h > 0 else "📉"
            change_sign = "+" if change_24h > 0 else ""
            msg = (
                f"\n<b>{symbol}:</b>\n"
                f"💵 <b>USD:</b> ${price_usd:,.2f}\n"
                f"🇷🇺 <b>RUB:</b> ₽{price_rub:,.2f}\n"
                f"{change_emoji} <b>24ч:</b> {change_sign}{change_24h:.2f}%\n"
                f"⏰ <i>Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</i>"
            )
            return msg
        else:
            return "❌ Не удалось получить данные."
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"

def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    btns = [types.InlineKeyboardButton(text=sym, callback_data=sym) for sym in TOP_COINS.keys()]
    kb.add(*btns)
    kb.add(types.InlineKeyboardButton(text="Обновить все", callback_data="refresh_all"))
    return kb

@bot.message_handler(commands=['start', 'menu'])
def welcome(msg):
    text = "\n👋 <b>Крипто Бот</b>\nВыбери монету ниже, чтобы узнать курс (USD/RUB):"
    bot.send_message(msg.chat.id, text, reply_markup=main_menu(), parse_mode='HTML')

@bot.message_handler(commands=['help'])
def help(msg):
    bot.reply_to(
        msg,
        "\nДоступны запросы: BTC, ETH, SOL, BNB, USDT, DOGE, TRX, TON, ADA, XRP.\n\n/start - меню\n/help - помощь\n/menu - главное меню\nИли выбери на клавиатуре."
    )

@bot.message_handler(func=lambda m: m.text and m.text.strip().upper() in TOP_COINS.keys())
def coin_price_text(msg):
    symbol = msg.text.strip().upper()
    coin_id = TOP_COINS[symbol]
    data = get_coin_price(coin_id, symbol)
    bot.send_message(msg.chat.id, data, parse_mode="HTML", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data in TOP_COINS.keys() or call.data == 'refresh_all')
def inline_btn(call):
    if call.data == 'refresh_all':
        coins = [get_coin_price(TOP_COINS[sym], sym) for sym in TOP_COINS.keys()]
        msg = '\n'.join(coins)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg, parse_mode='HTML', reply_markup=main_menu())
    else:
        coin_id = TOP_COINS[call.data]
        msg = get_coin_price(coin_id, call.data)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg, parse_mode='HTML', reply_markup=main_menu())

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
        return "OK"
    except Exception as err:
        return f"Error: {err}", 500

@app.route('/')
def root():
    return "Бот работает!"

if __name__ == '__main__':
    if WEBHOOK_URL:
        bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
        print(f"Webhook set on {WEBHOOK_URL}/webhook")
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
    else:
        bot.remove_webhook()
        print('Polling mode')
        bot.infinity_polling(none_stop=True)
