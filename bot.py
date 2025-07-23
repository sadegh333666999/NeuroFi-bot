import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# گرفتن اطلاعات قیمت از CoinGecko
def get_price_info(symbol):
    symbol = symbol.lower()
    mapping = {
        "btc": "bitcoin",
        "eth": "ethereum",
        "bnb": "binancecoin",
        "sol": "solana",
        "xrp": "ripple",
        "ada": "cardano",
        "doge": "dogecoin"
    }

    if symbol not in mapping:
        return "❌ نماد وارد شده پشتیبانی نمی‌شود."

    coin_id = mapping[symbol]
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false&sparkline=true"
    response = requests.get(url)
    data = response.json()

    try:
        price = data["market_data"]["current_price"]["usd"]
        change_24h = data["market_data"]["price_change_percentage_24h"]
        high_24h = data["market_data"]["high_24h"]["usd"]
        low_24h = data["market_data"]["low_24h"]["usd"]
        chart_link = f"https://www.coingecko.com/en/coins/{coin_id}"

        return (
            f"💰 {symbol.upper()} - قیمت لحظه‌ای: ${price:,}\n"
            f"📈 تغییر 24ساعته: {change_24h:.2f}%\n"
            f"🔺 بیشترین قیمت 24ساعته: ${high_24h:,}\n"
            f"🔻 کمترین قیمت 24ساعته: ${low_24h:,}\n"
            f"📊 چارت ساده: {chart_link}"
        )
    except:
        return "❌ دریافت اطلاعات با خطا مواجه شد."

# پاسخ به پیام‌ها
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    response = get_price_info(text)
    await update.message.reply_text(response)

# اجرای ربات
def main():
    token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
