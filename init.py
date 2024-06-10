from bson.int64 import Int64
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext, ContextTypes

from datetime import timedelta, datetime
import os
import pytz

load_dotenv()

from db import MongoConn
from chains import summary_chain

gmt2 = pytz.timezone('Europe/Madrid')

mongoConn = MongoConn('messages')

def get_current_week(date):
    # Asegurarse de que la fecha dada sea un objeto datetime
    if isinstance(date, datetime):
        given_date = date
    else:
        given_date = datetime.strptime(date, '%Y-%m-%d')

    # Obtener el lunes de la semana actual
    start_of_week = given_date - timedelta(days=given_date.weekday())
    # Obtener el domingo de la semana actual
    end_of_week = start_of_week + timedelta(days=6)

    return start_of_week, end_of_week

# Función para manejar mensajes
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    
    username = update.message.from_user.full_name
    if username == 'Pablo':
        username = 'Pablo' if update.message.from_user.username == 'pablodelucia' else 'Pout'

    user_id = update.message.from_user.id

    message_time = update.message.date.astimezone(gmt2)

    print(f"{update.message.from_user.first_name} - {update.message.text}")
    
    mongoConn.save({
        'chat_id': update.message.chat_id,
        'username': username,
        'user_id': user_id,
        'message_time': message_time,
        'message': update.message.text
    })


# Comando para mostrar estadísticas
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('##### Stats command #####')

    chat_id = Int64(update.message.chat_id)

    today_messages = mongoConn.read_by_datetime(datetime.now(), chat_id)
    total_messages = len(list(today_messages))
    message_per_user = mongoConn.get_msg_by_user(datetime.now(), chat_id)
    most_active_users = sorted(message_per_user, key=lambda x: x['count'], reverse=True)
        
    hours_message = ""
    for hour_counter in mongoConn.get_msg_by_hour(datetime.now(), chat_id):
        hours_message += f"🕰️ {int(hour_counter['_id'])+2:02d}:00 - {hour_counter['count']}\n"
    
    principal_contributors_message = ""
    icon = ['🥇', '🥈', '🥉'] + ['👥']*(len(most_active_users)-3)
    for i, user in enumerate(most_active_users):
        principal_contributors_message += f"{icon[i]} {user['username']}: {user['count']} mensajes {'🔥' if user['count']>100 else ''}\n"

    output = f"""💬 Resumen del Chat Diario 💬
📊 Estadísticas de {datetime.today().strftime('%d/%m/%Y')}

**Total de mensajes enviados hoy:** {total_messages} 📱

**Desglose Horario:**
{hours_message}

**Contribuyentes Principales:**
{principal_contributors_message}

¡Que el ritmo no pare! 💬"""

    # await update.message.reply_text(output_message)
    await update.message.reply_markdown(output)
    print('#'*15)

async def weekly_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = Int64(update.message.chat_id)
    stat_date, end_date = get_current_week(datetime.now())
    weekly_messages = len(
        list(
            mongoConn.read_by_daterange(stat_date, end_date, chat_id)
        )
    )
    await update.message.reply_markdown(
        f"Esta semana se han enviado {weekly_messages} mensajes 💬"
    )

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = Int64(update.message.chat_id)

    last_message_date = datetime.now() - timedelta(hours=2)
    half_hour_from_last_message_date = last_message_date - timedelta(minutes=30)

    messages = mongoConn.read_by_daterange(
        start_day=half_hour_from_last_message_date,
        end_day=last_message_date, 
        chat_id=chat_id
    )
    if len(messages) < 10:
        messages = mongoConn.read_all({'chat_id':chat_id}).sort('message_time', -1).limit(200)
    chat_messages = [f"{m.get('username')}: {m.get('message')}" for m in messages]
    chat_input = "\n".join(chat_messages)

    summary_text = summary_chain(chat_input)
    await update.message.reply_text(summary_text)


# Configurar el bot
def main():
    # Reemplaza 'YOUR_TOKEN' con el token de tu bot
    token = os.getenv('BOT_TOKEN')
    application = ApplicationBuilder().token(token).build()
    
    application.add_handler(MessageHandler((filters.TEXT | filters.Document.GIF | filters.Document.JPG | filters.Sticker.ALL )& ~filters.COMMAND, message_handler))
    application.add_handler(CommandHandler('stats', stats_command))
    application.add_handler(CommandHandler('weekly_stats', weekly_stats_command))
    application.add_handler(CommandHandler('summary', summary))
    application.add_handler(CommandHandler('resumen_pls', summary))

    application.run_polling(allowed_updates=Update.MESSAGE)

if __name__ == '__main__':
    main()