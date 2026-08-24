import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.ext import Flask, request, jsonify

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL_USERNAME", "@DutyCoinTAP")
GROUP = os.getenv("GROUP_USERNAME", "@DutyGroupCoin")
WEBAPP_URL = os.getenv("WEBAPP_URL", "").strip()

VALID = {"member", "administrator", "creator"}

def main_menu():
    rows = [
        [InlineKeyboardButton("🎮 PLAY DUTY", web_app=WebAppInfo(url=WEBAPP_URL))]
    ] if WEBAPP_URL.startswith("https://") else [
        [InlineKeyboardButton("⚠️ SET WEBAPP_URL FIRST", callback_data="no_url")]
    ]
    return InlineKeyboardMarkup(rows)

def join_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 JOIN DUTY COIN", url=f"https://t.me/{CHANNEL.lstrip('@')}")],
        [InlineKeyboardButton("💬 JOIN DUTY GROUP", url=f"https://t.me/{GROUP.lstrip('@')}")],
        [InlineKeyboardButton("✅ I'VE JOINED — CHECK", callback_data="check_membership")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎖️ *WELCOME TO DUTY*\n\n"
        "Your mission starts here.\n\n"
        "Join both official communities, then verify your membership.",
        parse_mode="Markdown",
        reply_markup=join_menu()
    )

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    try:
        cm = await context.bot.get_chat_member(CHANNEL, uid)
        gm = await context.bot.get_chat_member(GROUP, uid)
        if cm.status in VALID and gm.status in VALID:
            await q.edit_message_text(
                "🎖️ *ACCESS GRANTED*\n\nWelcome, Soldier. 🫡\n\nYour mission is ready.",
                parse_mode="Markdown",
                reply_markup=main_menu()
            )
        else:
            await q.answer("❌ Join both communities first.", show_alert=True)
    except Exception as e:
        print("Membership error:", repr(e))
        await q.answer("⚠️ Membership check failed. Confirm the bot is admin in both.", show_alert=True)

async def simple_command(update, context):
    mapping = {
        "profile": "👤 Open your profile in the Duty Mini App.",
        "daily": "🎁 Open Daily Reward in the Duty Mini App.",
        "friends": "👥 Open Friends in the Duty Mini App.",
        "ranking": "🏆 Open Ranking in the Duty Mini App.",
        "wallet": "💳 Open Wallet in the Duty Mini App.",
        "tasks": "🎯 Open Tasks in the Duty Mini App.",
        "boost": "⚡ Open Boost in the Duty Mini App.",
        "help": "❓ Use /start to enter Duty, then use the buttons inside the game."
    }
    cmd = update.message.text.lstrip("/").split("@")[0]
    await update.message.reply_text(mapping.get(cmd, "Open Duty with /start."))

async def no_url(update, context):
    await update.callback_query.answer("Set WEBAPP_URL to a public HTTPS Mini App URL first.", show_alert=True)

def run():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN missing in .env")
    app = Application.builder().token(BOT_TOKEN).proxy("socks5://10.0.0.2:2080").get_updates_proxy("socks5://10.0.0.2:2080").build()
    app.add_handler(CommandHandler("start", start))
    for cmd in ["profile","daily","friends","ranking","wallet","tasks","boost","help","play"]:
        app.add_handler(CommandHandler(cmd, simple_command))
    app.add_handler(CallbackQueryHandler(check, pattern="^check_membership$"))
    app.add_handler(CallbackQueryHandler(no_url, pattern="^no_url$"))
    print("DUTY BOT RUNNING...")
    app.run_polling()

if __name__ == "__main__":
    run()
