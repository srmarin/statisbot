from bson.int64 import Int64
from dotenv import load_dotenv
from matplotlib import pyplot as plt
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes, Defaults

import logging
from datetime import timedelta, datetime, time
import io
import os
import pytz

from utils import get_current_week

load_dotenv('../.env')

from constants import USERS, HOLIS_ID

from db import MongoConn
from chains import speech_to_text, summary_chain

gmt2 = pytz.timezone('Europe/Madrid')
HOURS_IN_KEYBOARD = (3, 7, 9, 11, 13, 15, 17, 19, 22, 24)
mongoConn = MongoConn('messages')


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Función para manejar mensajes
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    
    if update.edited_message is None:
        username = update.message.from_user.full_name
        
        if username == 'Pablo':
            username = 'Pablo' if update.message.from_user.username == 'pablodelucia' else 'Pout'

        user_id = update.message.from_user.id
        message_time = update.message.date.astimezone(gmt2)

        logger.info(f"{update.message.from_user.first_name} - {update.message.text}")

        mongoConn.save({
            'chat_id': update.message.chat_id,
            'username': username,
            'user_id': user_id,
            'message_time': message_time,
            'message': update.message.text
        })


# Comando para mostrar estadísticas
def stats_message(chat_id):
    logger.info('##### Stats command #####')

    chat_id = Int64(chat_id)

    today_messages = mongoConn.read_by_datetime(datetime.now(), chat_id)
    total_messages = len(list(today_messages))
    message_per_user = mongoConn.get_msg_by_user(datetime.now(), chat_id)
    most_active_users = sorted(message_per_user, key=lambda x: x['count'], reverse=True)
        
    hours_message = ""
    for hour_counter in mongoConn.get_msg_by_hour(datetime.now(), chat_id):
        hours_message += f"🕰️ {int(hour_counter['_id'])+2:02d}:00 \- {hour_counter['count']}\n"
    
    principal_contributors_message = ""
    icon = ['🥇', '🥈', '🥉'] + ['👥']*(len(most_active_users)-3)
    for i, user in enumerate(most_active_users):
        principal_contributors_message += f"{icon[i]} {user['username']}: {user['count']} mensajes {'🔥' if user['count']>100 else ''}\n"

    output = f"""💬 __*Resumen del Chat Diario*__ 💬
📊 *Estadísticas de {datetime.today().strftime('%d/%m/%Y')}*

*Total de mensajes enviados hoy:* {total_messages} 📱

*Desglose Horario:*
{hours_message}

*Contribuyentes Principales:*
{principal_contributors_message}

¡Que el ritmo no pare\! 💬"""

    # await update.message.reply_text(output_message)
    logger.info('#'*15)
    return output


def weekly_stats_message(chat_id):
    chat_id = Int64(chat_id)
    start_date, end_date = get_current_week(datetime.now())
    total_weekly_messages = len(list(mongoConn.read_by_daterange(start_date, end_date, chat_id)))
    
    group_message_by_hour = {}
    user_messages = {}
    for day in [start_date + timedelta(days=x) for x in range(7)]:
        for hour_counter in mongoConn.get_msg_by_hour(day, chat_id):
            key = int(hour_counter['_id'])+2 # +2 to fix hour datetime
            counter = int(hour_counter['count'])
            if key not in group_message_by_hour.keys():
                group_message_by_hour[key] = counter
            else:
                group_message_by_hour[key] += counter
            # hours_message += f"🕰️ {int(hour_counter['_id'])+2:02d}:00 - {hour_counter['count']}\n"
    
        message_per_user = mongoConn.get_msg_by_user(day, chat_id)
        most_active_users = sorted(message_per_user, key=lambda x: x['count'], reverse=True)
        for i, user in enumerate(most_active_users):
            if user['username'] in user_messages.keys():
                user_messages[user['username']] += user['count']
            else:
                user_messages[user['username']] = user['count']

    hours_message = ""
    for hour, count in sorted(group_message_by_hour.items()):
        hours_message += f"🕰️ {hour:02d}:00 \- {count}\n"
    
    user_stats_message = ""
    icon = ['🥇', '🥈', '🥉'] + ['👥']*(len(user_messages)-3)
    for i, (user, count) in enumerate(sorted(user_messages.items(),key=lambda x:x[1], reverse=True)):
        user_stats_message += f"{icon[i]} {user}: {count} mensajes {'🔥' if count > 1000 else ''}\n"

    output = f"""💬 __*Resumen del Chat Semanal*__ 💬
📊 *Estadísticas para semana {start_date.strftime('%d/%m/%Y')} \- {end_date.strftime('%d/%m/%Y')}*

*Total de mensajes enviados:* {total_weekly_messages} 📱

*Desglose Horario:*
{hours_message}

*Desglose por usuarios:*
{user_stats_message}

¡Que el ritmo no pare\! 💬"""
    
    return output
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    output = stats_message(update.message.chat_id)
    await update.message.reply_markdown_v2(output)

async def weekly_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat_id
    output = weekly_stats_message(chat_id)
    await update.message.reply_markdown_v2(output)

async def summary_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    options = [
            InlineKeyboardButton(f"{drange}:00 - {drange_next}:00", callback_data=f"{drange} {drange_next}") 
            for drange, drange_next in zip(HOURS_IN_KEYBOARD, HOURS_IN_KEYBOARD[1:]) if drange_next < datetime.now().hour+1
    ]
    keyboard = [
        options[:len(options)//2],
        options[len(options)//2:],
        [InlineKeyboardButton("Hasta ahora", callback_data='last -')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Elige una opción:", reply_markup=reply_markup)

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    
    chat_id = Int64(update.callback_query.message.chat_id)
    logger.info(query.message.chat_id)

    selected_hour, next_hour = query.data.split()
    today = datetime.today().replace(minute=0, second=0, microsecond=0)

    if selected_hour == 'last':
        open_range = today - timedelta(hours=2)
        close_range = datetime.now()
    else:
        open_range = today.replace(hour=int(selected_hour)-2)
        close_range = today.replace(hour=int(next_hour)-2, minute=59, second=59)

    logger.info(f"Buscando entre {open_range} y {close_range}")
    
    messages =list(mongoConn.read_by_daterange(
        start_day=open_range,
        end_day=close_range, 
        chat_id=chat_id
    ))

    logger.info(f"Cantidad de mensajes encontrados: {len(messages)}")

    header_message = f"Resumen entre {selected_hour}:00 y {next_hour}:00:\n" \
        if selected_hour != "last" else "Resumen del último tramo:\n"
    
    if len(messages) == 0:
        logger.info(f"No hay mensajes: {len(list(messages))}")
        await update.callback_query.message.reply_text(
            header_message + "No hay mensajes."
        )
        
        albo_sticker = 'CAACAgQAAxkBAAPWZmf6uvhxFHnhP1I9yEbCCk1Iaf8AAl8QAALzGmFSt4r9iyHeZNs1BA'
        await update.callback_query._bot.send_sticker(sticker=albo_sticker, chat_id=chat_id)
        
    else:

        chat_messages = [f"{m.get('username')}: {m.get('message')}" for m in messages]
        chat_input = "\n".join(chat_messages)

        summary_text = summary_chain(chat_input)

        await update.callback_query.message.reply_text(
            header_message + summary_text
        )

async def chart_per_person(update:Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) ==1:
        username = context.args[0]
        user_id = USERS.get(username)
    else:
        user_id = update.message.from_user.id
        username = "@"+update.message.from_user.username

    chat_id = update.message.chat_id

    user_list_message = mongoConn.get_message_by_hour_and_person(
        day=datetime.today(), 
        user_id=user_id,
        chat_id=chat_id
    )
    
    message_counter = [(message['_id']+2, message['count']) for message in user_list_message]
    x_axis, y_axis = map(list, zip(*message_counter)) # Day hours  x  Message grouped by hour

    figure = plt.figure()
    plt.bar(x_axis, y_axis, color='red', width=0.4)
    plt.xticks(range(min(x_axis), max(x_axis)+1))
    plt.xlabel("Horas de los mensajes")
    plt.ylabel(f"Número de mensajes de {username}")
    picture = io.BytesIO()
    plt.savefig(picture, format='png')
    picture.seek(0)
    graph_img = picture.read()

    await update.message.reply_photo(
        graph_img, 
        caption=f"Gráfica de mensajes de {username}"
    )
   
async def get_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message and update.message.reply_to_message.voice:
        voice_message = await  context.bot.get_file(update.message.reply_to_message.voice.file_id)
        # download the voice note as a file
        if not os.path.isdir('./voices'):
            os.mkdir('./voices/')
        voice_message_path = await voice_message.download_to_drive(f"./voices/{update.message.from_user.username.replace(' ', '-')}_{update.message.reply_to_message.voice.file_id}.ogg")
        voice_text = speech_to_text(str(voice_message_path))

        await update.message.reply_text(voice_text)
        try:
            os.remove(str(voice_message_path))
        except Exception as e:
            print(e)

    else:
        await update.message.reply_text("¿Cómo te voy a convertir a texto el audio si no has mandao audio?")

async def notify_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    notify_message = " ".join(USERS.keys())

    await update.message.reply_text(notify_message)

async def stats_job(context: ContextTypes.DEFAULT_TYPE):
    logger.info("##### LLega a ejecutarse el chron")
    message = stats_message(HOLIS_ID)
    await context.bot.send_message(text=message, chat_id=HOLIS_ID, parse_mode=ParseMode.MARKDOWN)

async def weekly_stats_job(context: ContextTypes.DEFAULT_TYPE):
    logger.info("##### Weekly stats ####")
    message = weekly_stats_message(HOLIS_ID)
    await context.bot.send_message(text=message, chat_id=HOLIS_ID, parse_mode=ParseMode.MARKDOWN)

# Configurar el bot
def main():
    # Reemplaza 'YOUR_TOKEN' con el token de tu bot
    token = os.getenv('BOT_TOKEN')
    defaults = Defaults(tzinfo=pytz.timezone('Europe/Madrid'))
    application = ApplicationBuilder().token(token).defaults(defaults).build()
    
    application.add_handler(MessageHandler(
        (filters.TEXT | filters.Document.GIF | filters.Document.JPG | filters.Sticker.ALL )& ~filters.COMMAND, 
        message_handler)
    )
    # application.add_handler(MessageHandler(filters.voice , get_voice_message))


    application.add_handler(CommandHandler('stats', stats_command))
    application.add_handler(CommandHandler('weekly_stats', weekly_stats_command))
    application.add_handler(CommandHandler('summary', summary_menu))
    application.add_handler(CommandHandler('resumen_pls', summary_menu))
    application.add_handler(CommandHandler('graph', chart_per_person))
    application.add_handler(CommandHandler('s2t', get_voice_message))
    application.add_handler(CommandHandler('all', notify_all))
    application.add_handler(CallbackQueryHandler(summary))

    application.job_queue.run_daily(stats_job, time(hour=23, minute=59, second=00))
    application.job_queue.run_daily(weekly_stats_job, time(hour=23, minute=59, second=00), days=[0])
    
    application.run_polling(allowed_updates=Update.MESSAGE)

if __name__ == '__main__':
    main()