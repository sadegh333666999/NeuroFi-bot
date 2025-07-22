import logging
import os
import json
import random
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.error import BadRequest

# ---------------- تنظیمات اولیه ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "referrals.json"
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

# ---------------- مدیریت فایل داده ----------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# ---------------- بررسی عضویت کاربر ----------------
async def is_user_member(user_id, context):
    for channel in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
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

    # ثبت دعوتی
    if context.args:
        inviter_id = context.args[0]
        if inviter_id != uid and uid not in data.get(inviter_id, {}).get("invited", []):
            data[inviter_id]["invited"].append(uid)
            save_data(data)

    # چک عضویت
    member = await is_user_member(user.id, context)
    if not member:
        text = (
            "❌ برای شروع، ابتدا در کانال‌های زیر عضو شوید:\n\n" +
            "\n".join([f"🔹 {ch}" for ch in REQUIRED_CHANNELS]) +
            "\n\nسپس دستور /start را دوباره ارسال کنید."
        )
        await update.message.reply_text(text)
        return

    # ارسال خوش‌آمد و لینک دعوت
    referral_link = f"https://t.me/{context.bot.username}?start={uid}"
    text = (
        "🧠 به دنیای NeuroFi خوش آمدید!\n\n"
        "📡 رسانه‌ی هوشمند اقتصاد نوین\n"
        "📊 تحلیل بازار | 🎯 سیگنال حرفه‌ای\n"
        "🎥 آموزش | 💸 انتقال ارز | 🎶 موزیک و آرامش\n\n"
        "✨ در دنیای ما، جاذبه به سمت بالاست...\n\n"
        "📨 لینک دعوت اختصاصی شما:\n"
        f"{referral_link}\n\n"
        "✅ برای استفاده از گردونه، روی دکمه زیر بزنید:"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎰 استفاده از گردونه", callback_data="spin")]
    ])
    await update.message.reply_text(text, reply_markup=keyboard)

# ---------------- هندل گردونه ----------------
async def spin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    uid = str(user.id)
    data = load_data()

    if uid not in data:
        await query.edit_message_text("❌ ابتدا باید /start را ارسال کنید.")
        return

    if not await is_user_member(user.id, context):
        await query.edit_message_text("❌ هنوز در همه‌ی کانال‌ها عضو نیستید. لطفاً عضو شوید و /start بزنید.")
        return

    invited_count = len(data[uid]["invited"])
    spin_count = data[uid].get("spin_count", 0)

    # بررسی شرط استفاده
    if spin_count == 0:
        allowed = True
    elif spin_count == 1 and invited_count >= 50:
        allowed = True
    elif spin_count >= 2 and invited_count >= (50 + 100 * (spin_count - 1)):
        allowed = True
    else:
        allowed = False

    if allowed:
        prize = random.choice(REWARD_LIST)
        data[uid]["spin_count"] += 1
        save_data(data)
        await query.edit_message_text(
            f"🎉 تبریک! شما برنده شدید:\n{prize}\n\n📥 حالا آدرس کیف پول خود را به صورت زیر ارسال کنید:\n`wallet: YOUR_ADDRESS`",
            parse_mode="Markdown"
        )
    else:
        needed = 50 if spin_count == 1 else (50 + 100 * (spin_count - 1))
        await query.edit_message_text(f"❌ برای استفاده از گردونه، باید حداقل {needed} نفر را دعوت کنید.\n📨 از لینک رفرال خود استفاده کنید.")

# ---------------- آدرس کیف پول ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id)
    text = update.message.text.strip()
    data = load_data()

    if text.startswith("wallet:"):
        address = text.replace("wallet:", "").strip()
        if uid in data:
            data[uid]["wallet"] = address
            save_data(data)
            await update.message.reply_text("✅ آدرس کیف پول شما ذخیره شد.")
        else:
            await update.message.reply_text("❌ ابتدا /start را ارسال کنید.")
    else:
        await update.message.reply_text("📩 لطفاً آدرس کیف پول را با فرمت زیر بفرستید:\n`wallet: YOUR_ADDRESS`", parse_mode="Markdown")

# ---------------- اجرا ----------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(spin_callback, pattern="^spin$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
