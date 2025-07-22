import os
import json
import random
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "referrals.json"
CHANNELS = ['@NeuroFi_Channel', '@Neuro_Fi']

REWARDS = [
    "🎁 NFT اختصاصی ۵۰ دلاری",
    "🎁 NFT اختصاصی ۱۰۰ دلاری",
    "🎁 NFT اختصاصی ۱۵۰ دلاری",
    "💸 ۵۰ توکن ECG",
    "💎 ۲ استار تلگرام",
    "🚀 ۱۰ ترون",
    "🐶 ۵۰,۰۰۰ شیبا",
    "🎫 اشتراک ۱ ماهه پریمیوم"
]

# ---------------- ذخیره‌سازی ----------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# ---------------- بررسی عضویت ----------------
async def check_membership(user_id, context):
    for ch in CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=ch, user_id=user_id)
            if member.status in ['left', 'kicked']:
                return False
        except:
            return False
    return True

# ---------------- /start ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id)
    data = load_data()

    # رفرال
    if uid not in data:
        data[uid] = {"invited": [], "wallet": "", "spin_count": 0}
    if context.args:
        inviter_id = context.args[0]
        if inviter_id != uid and uid not in data.get(inviter_id, {}).get("invited", []):
            if inviter_id not in data:
                data[inviter_id] = {"invited": [], "wallet": "", "spin_count": 0}
            data[inviter_id]["invited"].append(uid)
    save_data(data)

    # چک عضویت
    if not await check_membership(user.id, context):
        await update.message.reply_text("🛑 لطفاً ابتدا در کانال‌ها عضو شوید:\n" + "\n".join(CHANNELS))
        return

    # پیام خوش‌آمد + دکمه گردونه
    await update.message.reply_sticker("CAACAgUAAxkBAAEBxyzlZQ8sAAAEPbs_V_5RSO5ubEEXhgACZwEAAvcCyFDP56c6EN0zDDQE")

    referral_link = f"https://t.me/{context.bot.username}?start={uid}"
    msg = f"""
🧠 به دنیای NeuroFi خوش آمدید  
📊 آموزش | تحلیل | خدمات مالی | موزیک

🎁 برای دریافت جایزه:
1️⃣ عضو کانال‌ها شوید
2️⃣ دوستانتان را دعوت کنید
3️⃣ گردونه شانس را بچرخانید!

📨 لینک دعوت اختصاصی شما:
{referral_link}

🎯 مرحله اول: عضویت
🎯 مرحله دوم: دعوت ۵۰ نفر
🎯 مرحله سوم: دعوت ۱۰۰ نفر

✨ در دنیای ما... جاذبه به سمت بالاست 🚀
"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎰 چرخاندن گردونه", callback_data="spin")]
    ])
    await update.message.reply_text(msg, reply_markup=keyboard)

# ---------------- گردونه ----------------
async def spin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    uid = str(user.id)
    await query.answer()
    data = load_data()

    if uid not in data:
        await query.edit_message_text("لطفاً ابتدا /start را ارسال کنید.")
        return

    if not await check_membership(user.id, context):
        await query.edit_message_text("برای استفاده از گردونه، ابتدا عضو کانال‌ها شوید.")
        return

    invited = len(data[uid]["invited"])
    spin_count = data[uid].get("spin_count", 0)

    allow = (
        (spin_count == 0) or
        (spin_count == 1 and invited >= 50) or
        (spin_count == 2 and invited >= 100)
    )

    if not allow:
        needed = 50 if spin_count == 1 else 100
        await query.edit_message_text(f"🔁 برای مرحله بعدی، باید {needed} نفر دعوت کنید.")
        return

    # شبیه‌سازی لودینگ و جایزه
    await query.edit_message_text("🎡 در حال چرخاندن گردونه... لطفاً صبر کنید...")
    await asyncio.sleep(4)

    prize = random.choice(REWARDS)
    data[uid]["spin_count"] += 1
    save_data(data)

    await query.edit_message_text(
        f"🎉 گردونه چرخید!\n🏆 جایزه شما:\n{prize}\n\n"
        "📥 لطفاً آدرس کیف پول خود را با فرمت زیر ارسال کنید:\n`wallet: YOUR_ADDRESS`",
        parse_mode="Markdown"
    )

# ---------------- ذخیره آدرس کیف پول ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    msg = update.message.text.strip()
    data = load_data()

    if msg.lower().startswith("wallet:"):
        wallet = msg.replace("wallet:", "").strip()
        if uid in data:
            data[uid]["wallet"] = wallet
            save_data(data)
            await update.message.reply_text("✅ آدرس کیف پول شما ذخیره شد.\n🎯 تا حداکثر ۲۴ ساعت آینده بررسی می‌شود.")
        else:
            await update.message.reply_text("❗ ابتدا /start را بزنید.")
    else:
        await update.message.reply_text("📩 لطفاً آدرس کیف پول را با این فرمت بفرست:\n`wallet: YOUR_ADDRESS`", parse_mode="Markdown")

# ---------------- اجرا ----------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(spin_callback, pattern="^spin$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
