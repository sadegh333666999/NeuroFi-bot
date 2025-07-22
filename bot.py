import logging
import os
import json
import random
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)
from telegram.error import BadRequest

# ---------------- تنظیمات ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "referrals.json"
ADMIN_USERNAME = "@NeuroFi_Persian"

REQUIRED_CHANNELS = [
    "@NeuroFi_Channel",
    "@Neuro_Fi",
    "@Neurofi_signals",
    "@Neurofi_Crypto"
]

REWARD_LIST = [
    "🎁 NFT EpicLegend به ارزش ۵۰ دلار",
    "🎁 NFT EpicLegend به ارزش ۱۰۰ دلار",
    "🎁 NFT EpicLegend به ارزش ۱۵۰ دلار",
    "🪙 ۱۰۰ عدد توکن ECG",
    "🪙 ۱۰ عدد ترون (TRX)",
    "🐶 ۵۰۰۰۰ عدد شیبا (SHIB)",
    "💎 اکانت پریمیوم تلگرام ۱ ماهه",
    "🌟 ۲ استار تلگرام برای اهدای هدیه"
]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- مدیریت فایل ----------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# ---------------- بررسی عضویت در کانال‌ها ----------------
async def is_user_member(user_id, context):
    for channel in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(channel, user_id)
            if member.status in ['left', 'kicked']:
                return False
        except BadRequest:
            return False
    return True

# ---------------- دستور /start ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id)
    data = load_data()

    if uid not in data:
        data[uid] = {"invited": [], "wallet": "", "spin_count": 0}
        save_data(data)

    if context.args:
        inviter_id = context.args[0]
        if inviter_id != uid and uid not in data.get(inviter_id, {}).get("invited", []):
            data[inviter_id]["invited"].append(uid)
            save_data(data)

    if not await is_user_member(user.id, context):
        channels = "\n".join([f"🔹 {ch}" for ch in REQUIRED_CHANNELS])
        await update.message.reply_text(
            f"❌ ابتدا در کانال‌های زیر عضو شوید:\n\n{channels}\n\nسپس /start را دوباره بزنید."
        )
        return

    referral_link = f"https://t.me/{context.bot.username}?start={uid}"
    welcome_text = (
        "🧠 به دنیای NeuroFi خوش آمدید!\n"
        "📊 آموزش | سیگنال | موزیک ترید | خدمات مالی\n"
        "✨ در دنیای ما، جاذبه به سمت بالاست...\n\n"
        "📨 لینک اختصاصی شما:\n"
        f"{referral_link}\n\n"
        "🎰 برای شرکت در گردونه، دکمه زیر را بزنید:"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎰 استفاده از گردونه", callback_data="spin")]
    ])
    await update.message.reply_text(welcome_text, reply_markup=keyboard)

# ---------------- گردونه ----------------
async def spin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    uid = str(user.id)
    data = load_data()

    if uid not in data:
        await query.edit_message_text("❌ ابتدا /start را بزنید.")
        return

    if not await is_user_member(user.id, context):
        await query.edit_message_text("❌ هنوز در کانال‌ها عضو نیستید.")
        return

    invited = len(data[uid]["invited"])
    spin_count = data[uid].get("spin_count", 0)

    if spin_count == 0:
        allowed = True
    elif spin_count == 1 and invited >= 50:
        allowed = True
    elif spin_count >= 2 and invited >= (50 + (spin_count - 1) * 100):
        allowed = True
    else:
        allowed = False

    if allowed:
        prize = random.choice(REWARD_LIST)
        data[uid]["spin_count"] += 1
        data[uid]["last_prize"] = prize
        save_data(data)

        await query.edit_message_text(
            f"🎉 تبریک! شما برنده شدید:\n{prize}\n\n"
            "📥 حالا آدرس کیف پول خود را به صورت زیر ارسال کنید:\n"
            "`wallet: YOUR_ADDRESS (شبکه)`",
            parse_mode="Markdown"
        )
    else:
        needed = 50 if spin_count == 1 else 50 + 100 * (spin_count - 1)
        await query.edit_message_text(
            f"❌ برای استفاده‌ی بعدی از گردونه باید حداقل {needed} نفر را دعوت کنید.\n"
            "📨 لینک دعوت خود را از /start بگیرید و به دوستانتان بدهید."
        )

# ---------------- ثبت کیف پول ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id)
    text = update.message.text.strip()
    data = load_data()

    if text.startswith("wallet:"):
        wallet = text.replace("wallet:", "").strip()

        if uid in data:
            data[uid]["wallet"] = wallet
            save_data(data)

            await update.message.reply_text(
                "✅ آدرس کیف پول شما ذخیره شد.\n"
                "🧾 لطفاً مطمئن شوید شبکه و نوع ارز صحیح انتخاب شده باشد.\n"
                "🎯 مثال: wallet: TRX_TQ7r..."
            )

            prize = data[uid].get("last_prize", "❓ مشخص نشده")
            admin_text = (
                f"🎉 کاربر جدید جایزه گرفت!\n"
                f"👤 نام: {user.first_name} (@{user.username})\n"
                f"🆔 آیدی عددی: {uid}\n"
                f"🎁 جایزه: {prize}\n"
                f"💼 آدرس کیف پول: {wallet}"
            )
            await context.bot.send_message(chat_id=ADMIN_USERNAME, text=admin_text)
        else:
            await update.message.reply_text("❌ ابتدا /start را بزنید.")
    else:
        await update.message.reply_text(
            "📩 لطفاً آدرس کیف پول را با فرمت زیر ارسال کنید:\n"
            "`wallet: NETWORK_ADDRESS`\n"
            "مثال: `wallet: TRX_TQ7r...`",
            parse_mode="Markdown"
        )

# ---------------- اجرا ----------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(spin_callback, pattern="^spin$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
