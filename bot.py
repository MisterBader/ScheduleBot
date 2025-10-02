import json
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

# Завантаження конфігів
with open("config.json") as f:
    config = json.load(f)
TOKEN = config["TOKEN"]

SCHEDULE_FILE = "schedules.json"
ADMINS_FILE = "admins.json"

# Функції для збереження/завантаження
def load_json(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return {}

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# Завантаження даних
schedules = load_json(SCHEDULE_FILE)
admins = load_json(ADMINS_FILE)

# Створення бота
app = ApplicationBuilder().token(TOKEN).build()

# /today
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today_str = datetime.now().strftime("%d.%m.%Y")
    text = schedules.get(today_str, "Розклад на сьогодні відсутній")
    await update.message.reply_text(text)

# /tomorrow
async def tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y")
    text = schedules.get(tomorrow_str, "Розклад на завтра відсутній")
    await update.message.reply_text(text)

# /data
async def data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Використання: /data ДД.ММ.РРРР")
        return
    date = context.args[0]
    text = schedules.get(date, f"Розклад на {date} відсутній")
    await update.message.reply_text(text)

# /edit
EDIT_DATE, EDIT_TEXT, EDIT_PASS = range(3)
async def edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Використання: /edit ДД.ММ.РРРР")
        return ConversationHandler.END
    context.user_data["date"] = context.args[0]
    await update.message.reply_text("Введіть код адміністратора:")
    return EDIT_PASS

async def edit_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text
    user_id = str(update.effective_user.id)
    if code == "30193019":
        context.user_data["is_super"] = True
        context.user_data["admin_name"] = "Mega Night"
    else:
        context.user_data["is_super"] = False
        context.user_data["admin_name"] = f"Адмін {user_id}"
    await update.message.reply_text("Введіть текст розкладу:")
    return EDIT_TEXT

async def edit_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date = context.user_data["date"]
    schedules[date] = update.message.text + f"\n\n(Змінив: {context.user_data['admin_name']})"
    save_json(SCHEDULE_FILE, schedules)
    await update.message.reply_text(f"Розклад на {date} оновлено.")
    return ConversationHandler.END

edit_conv = ConversationHandler(
    entry_points=[CommandHandler("edit", edit_start)],
    states={
        EDIT_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_pass)],
        EDIT_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_text)],
    },
    fallbacks=[]
)
app.add_handler(edit_conv)

# /admins для супер-адміна
ADMIN_ADD, ADMIN_EDIT, ADMIN_REMOVE = range(3)
async def admins_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Команди: /adminadd, /adminedit, /adminremove, /adminlist")
# Для простоти, команди можна додати тут аналогічно

app.add_handler(CommandHandler("admins", admins_start))
app.add_handler(CommandHandler("today", today))
app.add_handler(CommandHandler("tomorrow", tomorrow))
app.add_handler(CommandHandler("data", data))

print("Бот запущений!")
app.run_polling()
