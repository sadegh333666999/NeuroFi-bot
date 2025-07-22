import logging
import os
import random
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# فعال کردن لاگ‌گیری
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# تنظیمات اولیه
TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "referrals.json"

REWARD_LIST = [
    "🎁 NFT EpicLegend 50 دلاری",
    "🎁 NFT EpicLegend 100 دلاری",
    "🎁 NFT EpicLegend 150 دلاری",
    "🪙 توکن ECG",
    "🪙 ترون",
    "🐶 شیبا",
    "💎 اکانت پریمیوم تلگرام",
    "🌟 استار تلگرام"
]

# بارگذاری داده‌ها از فایل
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

# ذخیره‌سازی داده‌ها در فایل
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# دستور /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id)
    data = load_data()
    if uid not in data:
        data[uid] = {"invited": [], "wallet": "", "rewarded": False}
        save_data(data)

    referral_link = f"https://t.me/{context.bot.username}?start={uid}"
    msg = (
        "🧠 به دنیای NeuroFi خوش آمدید!\n"
        "🚀 در دنیای ما جاذبه به سمت بالاست\n\n"
        "🎁 برای دریافت جایزه:\n"
        "1. این ربات را به ۵۰ نفر معرفی کنید\n"
        "2. یا از گردونه شانس استفاده کنید\n"
        f"🔗 لینک دعوت اختصاصی شما:\n{referral_link}"
    )
    await update.message.reply_text(msg)

# گرفتن آدرس کیف پول
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id)
    text = update.message.text.strip()
    data = load_data()

    if text.startswith("wallet:"):
        wallet = text.replace("wallet:", "").strip()
        data[uid]["wallet"] = wallet
        save_data(data)
        await update.message.reply_text("✅ آدرس کیف پول شما ذخیره شد.")
    else:
        await update.message.reply_text("📩 لطفاً آدرس کیف پول را با فرمت زیر ارسال کنید:\nwallet: YOUR_ADDRESS")

# گردونه شانس
async def spin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id)
    data = load_data()
    if uid in data and not data[uid]["rewarded"]:
        prize = random.choice(REWARD_LIST)
        data[uid]["rewarded"] = True
        save_data(data)
        await update.message.reply_text(
            f"🎉 تبریک! شما برنده شدید:\n{prize}\n\n📥 حالا آدرس کیف پول خود را ارسال کنید:\nwallet: YOUR_ADDRESS"
        )
    else:
        await update.message.reply_text("❌ شما قبلاً از گردونه استفاده کرده‌اید یا ثبت‌نام نکرده‌اید.")

# اجرای ربات
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("spin", spin))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
