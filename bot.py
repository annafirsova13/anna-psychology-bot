from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3
import time
import os

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = os.environ.get('BOT_TOKEN', '7967826497:AAEU69plwGVYm4nbyl-eSkgQuebSI8u4DDU')
CHANNEL_USERNAME = "@annafirsova_psy"

# ========== БАЗА ДАННЫХ ==========
def init_db():
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, 
                  subscribed INTEGER DEFAULT 0, 
                  current_lesson INTEGER DEFAULT 0,
                  last_activity INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

def get_user_data(user_id):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result

def update_user_progress(user_id, subscribed=None, current_lesson=None):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    
    c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    existing = c.fetchone()
    
    if existing:
        new_subscribed = subscribed if subscribed is not None else existing[1]
        new_lesson = current_lesson if current_lesson is not None else existing[2]
        
        c.execute('''UPDATE users 
                    SET subscribed = ?, current_lesson = ?, last_activity = ?
                    WHERE user_id = ?''',
                 (new_subscribed, new_lesson, int(time.time()), user_id))
    else:
        c.execute('''INSERT INTO users 
                    (user_id, subscribed, current_lesson, last_activity) 
                    VALUES (?, ?, ?, ?)''',
                 (user_id, 
                  subscribed if subscribed is not None else 0,
                  current_lesson if current_lesson is not None else 0,
                  int(time.time())))
    
    conn.commit()
    conn.close()

# ========== ПРОВЕРКА ПОДПИСКИ ==========
async def check_subscription(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# ========== КОМАНДА /START ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    
    if user_data and user_data[1]:  # Если уже подписан
        current_lesson = user_data[2] if user_data[2] else 1
        if current_lesson >= 4:
            await show_final_offer(update, context)
        else:
            await show_lesson(update, context, current_lesson)
    else:
        await send_intro(update, context)

# ========== ПРИВЕТСТВИЕ С ВИДЕО-ЗНАКОМСТВОМ ==========
async def send_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    intro_text = (
        "Привет, дорогой друг 💫\n"
        "Я Анна Фирсова.\n"
        "Психолог, который на себе проверила, что значит — изменить жизнь ⚡️\n\n"
        
        "Раньше: страхи, сомнения, «а что подумают?» 🥺\n"
        "Сейчас: уверенность, действие, жизнь по своим правилам 🔥\n\n"
        
        "Всё благодаря мета-персональной терапии — подходу, который я сначала испытала на себе, а потом научилась помогать другим.\n\n"
        
        "❓Есть что-то, что ты хочешь изменить, но пока не получается?\n"
        "❓Боишься?\n"
        "❓Откладываешь?\n\n"
        
        "Начни с моего видео-знакомства 👇 — увидишь, что всё возможно!"
    )
    
    keyboard = [
        [InlineKeyboardButton("🎬 Смотреть видео-знакомство", url="https://kinescope.io/6SXEyHaosAxbhUa5sLg5G6")],
        [InlineKeyboardButton("✅ Посмотрел(а) видео", callback_data='intro_watched')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(intro_text, reply_markup=reply_markup)

# ========== ПРОСЬБА О ПОДПИСКЕ ==========
async def ask_for_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Узнал(а) в чем-то себя? 💫\n"
        "Хочешь также чувствовать опору внутри, даже когда кажется, что мир шатается?\n\n"
        
        "Все изменения начинаются с тебя.\n"
        "И я хочу подарить тебе первый ключ — тот, что поможет вернуть почву под ногами уже сегодня.\n\n"
        
        "Готов(а) сделать этот шаг?\n"
        "Твой первый урок ждет тебя 👇"
    )
    
    keyboard = [
        [InlineKeyboardButton("📢 Подписаться на канал", url=f'https://t.me/{CHANNEL_USERNAME[1:]}')],
        [InlineKeyboardButton("✅ Я подписался", callback_data='check_subscription')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=reply_markup
    )

# ========== ОТПРАВКА УРОКОВ ==========
async def show_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE, lesson_number: int):
    user_id = update.effective_user.id
    
    # Проверяем подписку
    if not await check_subscription(user_id, context):
        await ask_for_subscription(update, context)
        return
    
    lessons = {
        1: {
            "title": "Ключ 1: Внутренняя опора",
            "video_url": "https://kinescope.io/mVTuDwmpPVfLQqERy7K6Hv",
            "next_callback": "lesson1_watched",
            "description": "Первый ключ к твоей внутренней силе 🗝️"
        },
        2: {
            "title": "Ключ 2: Доступ к энергии", 
            "video_url": "https://kinescope.io/rRJru2PkuogPcZmVDap9K9",
            "next_callback": "lesson2_watched",
            "description": "Второй ключ: находи энергию внутри 🔋"
        },
        3: {
            "title": "Ключ 3: Режим «Мои правила!»", 
            "video_url": "https://kinescope.io/v6NC6HtWKQhGdEn3bgJ1oL",
            "next_callback": "lesson3_watched",
            "description": "Третий ключ: защити свою энергию 🛡️"
        }
    }
    
    lesson = lessons[lesson_number]
    
    # Отправляем урок с кнопкой просмотра
    keyboard = [
        [InlineKeyboardButton("🎬 Смотреть урок", url=lesson["video_url"])],
        [InlineKeyboardButton("✅ Я посмотрел(а) видео", callback_data=lesson["next_callback"])]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"🎬 {lesson['title']}\n\n{lesson['description']}\n\nНажми кнопку ниже чтобы посмотреть урок 👇"
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=reply_markup
    )

# ========== СООБЩЕНИЯ ПОСЛЕ УРОКОВ ==========
async def send_after_lesson_message(update: Update, context: ContextTypes.DEFAULT_TYPE, lesson_number: int):
    user_id = update.effective_user.id
    
    messages = {
        1: (
            "Отличная работа! Ты только что сделал(а) первый и самый важный шаг — начал(а) инвестировать в себя. 💫\n\n"
            
            "А теперь давай закрепим результат. Ответь себе честно, можно даже вслух или в заметках:\n"
            "🌟 Получилось ли попрактиковаться? Хотя бы минуту?\n"
            "🌟 Что изменилось в ощущениях? Может, стало чуть спокойнее или появилось чувство опоры?\n"
            "🌟 Какой самый главный инсайт ты вынес(ла) для себя?\n\n"
            
            "А теперь представь на секунду:\n"
            "Если бы в любой сложной ситуации ты мог(ла) вспомнить, что ТЫ — твоя главная опора... что бы изменилось в твоей жизни?\n\n"
            
            "Эта мысль — уже огромная сила. Сохрани это ощущение.\n\n"
            "А тебя уже ждет второй ключ, как будешь готов(а) - мы пойдем еще дальше. А пока — гордись собой, ты молодец! 🗝️"
        ),
        2: (
            "Отлично! Ты только что узнал(а), как находить энергию там, где раньше видел(а) только пустоту. Это настоящая суперсила! 🔋✨\n\n"
            
            "Давай закрепим это ощущение. Возьми паузу и спроси себя:\n\n"
            "💬 Удалось ли почувствовать разницу между состоянием «надо» и «я выбираю»?\n"
            "💬 В какой момент сегодня ты смог(ла) переключиться с выживания на осознанное действие?\n"
            "💬 Если бы каждое утро ты просыпался(ась) с доступом к этому источнику сил — какой бы стал твой завтрашний день?\n\n"
            
            "Запомни: твоя энергия всегда с тобой. Иногда она просто ждет, когда ты вспомнишь, где находится твой внутренний выключатель.\n\n"
            "А в следующем уроке мы сделаем последний, но самый важный шаг: я научу тебя, как беречь эти силы и направлять их на то, что действительно важно для тебя. Чтобы энергия не утекала в чужие дела и долги.\n\n"
            "Гордись собой — ты уже на полпути к себе обновленному! Жду тебя в третьем ключе. 🗝️"
        ),
        3: (
            "Ты прошел(ла) огромный путь за эти три шага! 🎉\n"
            "Ты обрел(ла) опору, нашёл(ла) источник энергии и научился(ась) беречь её. Теперь у тебя есть целый арсенал для изменений.\n\n"
            
            "А знаешь, что самое крутое? Это только начало.\n\n"
            
            "Если ты чувствуешь, что хочешь:\n"
            "✨ Систематизировать эти знания\n"
            "✨ Углубить практики и получить больше инструментов\n"
            "✨ Сделать уверенность своим постоянным состоянием\n\n"
            "— у меня есть два варианта продолжить наш путь:"
        )
    }
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=messages[lesson_number]
    )
    
    if lesson_number < 3:
        # Для уроков 1 и 2 - кнопка для следующего урока
        keyboard = [[InlineKeyboardButton(f"🚀 Перейти к ключу {lesson_number + 1}", callback_data=f'lesson_{lesson_number + 1}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Готов(а) двигаться дальше?",
            reply_markup=reply_markup
        )
    else:
        # Для урока 3 - финальное предложение
        await show_final_offer(update, context)

# ========== ФИНАЛЬНОЕ ПРЕДЛОЖЕНИЕ ==========
async def show_final_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💎 Уверенность в себе за 5 шагов", url="https://annafirsova-psy.ru/you_can")],
        [InlineKeyboardButton("🎁 Бесплатная диагностика", callback_data='free_consultation')],
        [InlineKeyboardButton("💌 Написать психологу", callback_data='contact_psychologist')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "💎 **Практический онлайн-курс «Уверенность в себе за 5 шагов»** — глубокая проработка, которая закрепит твои результаты и выведет на новый уровень. И там кстати первый урок - БЕСПЛАТНЫЙ! 🔥\n\n"
        "🕊️ **Бесплатная диагностическая консультация** (до 30 минут) — разберем твою текущую ситуацию, определим основные сложности, наметим план работы.\n\n"
        "Выбирай, что откликается, и давай расти вместе!"
    )
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ========== ОБРАБОТЧИК КНОПОК ==========
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    callback_data = query.data
    
    if callback_data == 'intro_watched':
        await query.edit_message_text("✅ Отлично! Теперь давай двигаться дальше!")
        await ask_for_subscription(update, context)
    
    elif callback_data == 'check_subscription':
        if await check_subscription(user_id, context):
            update_user_progress(user_id, subscribed=1, current_lesson=1)
            await query.edit_message_text("🎉 Спасибо за подписку! Вот твой первый урок:")
            await show_lesson(update, context, 1)
        else:
            await query.edit_message_text(
                "❌ Подписка не найдена. Пожалуйста, подпишись на канал и нажми проверку снова.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📢 Подписаться", url=f'https://t.me/{CHANNEL_USERNAME[1:]}')],
                    [InlineKeyboardButton("✅ Проверить подписку", callback_data='check_subscription')]
                ])
            )
    
    elif callback_data == 'lesson1_watched':
        update_user_progress(user_id, current_lesson=2)
        await query.edit_message_text("✅ Отлично! Первый ключ получен!")
        await send_after_lesson_message(update, context, 1)
    
    elif callback_data == 'lesson2_watched':
        update_user_progress(user_id, current_lesson=3)
        await query.edit_message_text("✅ Прекрасно! Второй ключ освоен!")
        await send_after_lesson_message(update, context, 2)
    
    elif callback_data == 'lesson3_watched':
        update_user_progress(user_id, current_lesson=4)
        await query.edit_message_text("✅ Браво! Все три ключа у тебя!")
        await send_after_lesson_message(update, context, 3)
    
    elif callback_data.startswith('lesson_'):
        lesson_number = int(callback_data.split('_')[1])
        user_data = get_user_data(user_id)
        if user_data and user_data[2] >= lesson_number:
            await show_lesson(update, context, lesson_number)
        else:
            await query.answer("Сначала заверши предыдущий урок!", show_alert=True)
    
    elif callback_data == 'free_consultation':
        keyboard = [
            [InlineKeyboardButton("💎 Курс «Уверенность в себе»", url="https://annafirsova-psy.ru/you_can")],
            [InlineKeyboardButton("💌 Написать в Telegram", url="https://t.me/annq13")],
            [InlineKeyboardButton("🌐 Мой сайт", url="https://annafirsova-psy.ru/")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🎁 **Бесплатная диагностическая консультация**\n\n"
            "За 30 минут мы:\n"
            "• Разберем твою текущую ситуацию\n"
            "• Определим основные сложности\n"
            "• Наметим план работы\n\n"
            "📅 Для записи напиши мне в Telegram: @annq13\n\n"
            "Напиши, пожалуйста, в сообщении кодовое слово «СИЛА»\n\n"
            "Также ты можешь:",
            reply_markup=reply_markup
        )
    
    elif callback_data == 'contact_psychologist':
        keyboard = [
            [InlineKeyboardButton("💎 Курс «Уверенность в себе»", url="https://annafirsova-psy.ru/you_can")],
            [InlineKeyboardButton("🎁 Бесплатная диагностика", callback_data='free_consultation')],
            [InlineKeyboardButton("🌐 Мой сайт", url="https://annafirsova-psy.ru/")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "💌 **Связь с психологом**\n\n"
            "Для консультации или вопросов:\n\n"
            "📱 Telegram: @annq13\n"
            "🌐 Сайт: https://annafirsova-psy.ru/\n\n"
            "Работаю онлайн по всему миру! 🌍\n\n"
            "Также ты можешь:",
            reply_markup=reply_markup
        )

# ========== ЗАПУСК БОТА ==========
def main():
    init_db()
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    print("✨ Бот запущен! Теперь он ждет твоих клиентов!")
    application.run_polling()

if __name__ == '__main__':
    main()