#!/usr/bin/env python3
# coding: utf-8

import os
import logging
import random
import string
import asyncio
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler,
    filters, ConversationHandler
)
import aiosqlite

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Set BOT_TOKEN in .env")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

DB_PATH = "santa_bot.db"

# Conversation states for profile/wishlist flows
(PROFILE_NAME, PROFILE_BIO, WL_ADD_NAME, WL_ADD_DESC, WL_ADD_PHOTO) = range(5)

# ---------- Database helper ----------
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
        PRAGMA foreign_keys = ON;
        CREATE TABLE IF NOT EXISTS users (
            tg_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS profiles (
            tg_id INTEGER PRIMARY KEY,
            fio TEXT,
            bio TEXT,
            FOREIGN KEY(tg_id) REFERENCES users(tg_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS wishlist_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER,
            game_code TEXT NULL,
            title TEXT,
            description TEXT,
            photo_file_id TEXT NULL,
            created_at TEXT,
            FOREIGN KEY(tg_id) REFERENCES users(tg_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS games (
            code TEXT PRIMARY KEY,
            organizer_id INTEGER,
            title TEXT,
            draw_date TEXT,
            min_participants INTEGER,
            created_at TEXT,
            is_drawn INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_code TEXT,
            tg_id INTEGER,
            joined_at TEXT,
            FOREIGN KEY(game_code) REFERENCES games(code) ON DELETE CASCADE,
            FOREIGN KEY(tg_id) REFERENCES users(tg_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS assignments (
            game_code TEXT,
            santa_id INTEGER,
            recipient_id INTEGER,
            PRIMARY KEY (game_code, santa_id),
            FOREIGN KEY(game_code) REFERENCES games(code) ON DELETE CASCADE,
            FOREIGN KEY(santa_id) REFERENCES users(tg_id) ON DELETE CASCADE,
            FOREIGN KEY(recipient_id) REFERENCES users(tg_id) ON DELETE CASCADE
        );
        """)
        await db.commit()

# ---------- Utility ----------
def gen_code(length=6):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))

async def ensure_user(db, tg_user):
    # insert or update basic user info
    await db.execute("""
        INSERT INTO users (tg_id, username, first_name, last_name, created_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(tg_id) DO UPDATE SET username=excluded.username, first_name=excluded.first_name, last_name=excluded.last_name
    """, (tg_user.id, tg_user.username or "", tg_user.first_name or "", tg_user.last_name or "", datetime.utcnow().isoformat()))
    await db.commit()

# ---------- Command handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    async with aiosqlite.connect(DB_PATH) as db:
        await ensure_user(db, user)
    await update.message.reply_text(
        "Привет! Ты зарегистрирован.\n"
        "Используй /help чтобы увидеть команды.\n\n"
        "Чтобы создать профиль (ФИО и био) — введите /profile"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
"/start — регистрация\n"
        "/profile — создать/редактировать профиль\n"
        "/wishlist — управлять вишлистом\n"
        "/create_game — создать игру (организатор)\n"
        "/join <КОД> — присоединиться к игре\n"
        "/leave <КОД> — выйти из игры\n"
        "/status <КОД> — статус игры (организатор или любой участник)\n"
        "/mix <КОД> или /send <КОД> — организатор запускает жеребьёвку\n"
        "/my_recipient <КОД> — посмотреть своего получателя (после розыгрыша)\n"
        "/ask <КОД> <сообщение> — отправить анонимный вопрос своему получателю\n"
    )
    await update.message.reply_text(text)

# ---------- Profile flow ----------
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите ФИО (имя фамилия):")
    return PROFILE_NAME

async def profile_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fio = update.message.text.strip()
    context.user_data['fio'] = fio
    await update.message.reply_text("Введите короткую биографию (хобби, интересы):")
    return PROFILE_BIO

async def profile_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bio = update.message.text.strip()
    tg_id = update.effective_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO profiles (tg_id, fio, bio) VALUES (?, ?, ?)",
                         (tg_id, context.user_data.get('fio'), bio))
        await db.commit()
    await update.message.reply_text("Профиль сохранён.")
    return ConversationHandler.END

async def cancel_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

# ---------- Wishlist flow ----------
async def wishlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Вишлист — команды:\n"
        "/wl_add — добавить пункт\n"
        "/wl_list — показать ваш вишлист\n"
        "/wl_clear — удалить все пункты\n"
    )
    await update.message.reply_text(text)

async def wl_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите название подарка:")
    return WL_ADD_NAME

async def wl_add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['wl_title'] = update.message.text.strip()
    await update.message.reply_text("Введите описание подарка:")
    return WL_ADD_DESC

async def wl_add_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['wl_desc'] = update.message.text.strip()
    await update.message.reply_text("Пришлите фотографию (или напишите /skip если без фото).")
    return WL_ADD_PHOTO

async def wl_add_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    photo = update.message.photo
    file_id = None
    if photo:
        file_id = photo[-1].file_id
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO wishlist_items (tg_id, title, description, photo_file_id, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (tg_id, context.user_data.get('wl_title'), context.user_data.get('wl_desc'), file_id, datetime.utcnow().isoformat()))
        await db.commit()
    await update.message.reply_text("Пункт добавлен в вишлист.")
    return ConversationHandler.END

async def wl_skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO wishlist_items (tg_id, title, description, photo_file_id, created_at)
            VALUES (?, ?, ?, NULL, ?)
        """, (tg_id, context.user_data.get('wl_title'), context.user_data.get('wl_desc'), datetime.utcnow().isoformat()))
        await db.commit()
    await update.message.reply_text("Пункт добавлен в вишлист (без фото).")
    return ConversationHandler.END

async def wl_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id, title, description, photo_file_id FROM wishlist_items WHERE tg_id = ?", (tg_id,))
        rows = await cur.fetchall()
    if not rows:
        await update.message.reply_text("Ваш вишлист пуст.")
        return
    messages = []
    media = []
    for r in rows:
        item_id, title, desc, file_id = r
        messages.append(f"{item_id}. {title}\n{desc}")
        if file_id:
            media.append(InputMediaPhoto(media=file_id, caption=title + "\n" + desc))
    # отправить текстовый список и затем медиа (если есть)
    await update.message.reply_text("\n\n".join(messages))
    if media:
        # telegram supports album up to 10 items
        for i in range(0, len(media), 10):
            await update.message.reply_media_group(media[i:i+10])

async def wl_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM wishlist_items WHERE tg_id = ?", (tg_id,))
        await db.commit()
    await update.message.reply_text("Вишлист очищен.")

# ---------- Game creation and management ----------
async def create_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Expect: /create_game <title> ; interactive minimal: we'll parse args
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Использование: /create_game <название_игры> <YYYY-MM-DD> [min_participants]\nПример: /create_game SecretSanta 2025-12-20 3")
        return
    title = args[0]
    date_str = args[1]
    try:
        draw_date = datetime.fromisoformat(date_str)
    except Exception:
        await update.message.reply_text("Неверная дата. Используйте формат YYYY-MM-DD")
        return
    min_p = 3
    if len(args) >= 3:
        try:
            min_p = max(3, int(args[2]))
        except:
            pass
    code = gen_code(6)
    tg_id = update.effective_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        await ensure_user(db, update.effective_user)
        await db.execute("""
            INSERT INTO games (code, organizer_id, title, draw_date, min_participants, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (code, tg_id, title, draw_date.isoformat(), min_p, datetime.utcnow().isoformat()))
        # organizer auto joins
        await db.execute("INSERT INTO participants (game_code, tg_id, joined_at) VALUES (?, ?, ?)",
                         (code, tg_id, datetime.utcnow().isoformat()))
        await db.commit()
    await update.message.reply_text(f"Игра создана.\nКод: {code}\nНазвание: {title}\nДата жеребьёвки: {draw_date.date()}\nМинимум участников: {min_p}\n\nИспользуйте /join {code} для присоединения других участников.\nОрганизатор может запустить жеребьёвку: /mix {code}")

async def join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /join <КОД>")
        return
    code = context.args[0].upper()
    tg_id = update.effective_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        await ensure_user(db, update.effective_user)
        cur = await db.execute("SELECT code FROM games WHERE code = ?", (code,))
        if not await cur.fetchone():
            await update.message.reply_text("Игра с таким кодом не найдена.")
            return
        # check already joined
        cur = await db.execute("SELECT 1 FROM participants WHERE game_code = ? AND tg_id = ?", (code, tg_id))
        if await cur.fetchone():
            await update.message.reply_text("Вы уже участник этой игры.")
            return
        await db.execute("INSERT INTO participants (game_code, tg_id, joined_at) VALUES (?, ?, ?)",
                         (code, tg_id, datetime.utcnow().isoformat()))
        await db.commit()
    await update.message.reply_text(f"Вы присоединились к игре {code}.")

async def leave_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
await update.message.reply_text("Использование: /leave <КОД>")
        return
    code = context.args[0].upper()
    tg_id = update.effective_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT is_drawn FROM games WHERE code = ?", (code,))
        row = await cur.fetchone()
        if not row:
            await update.message.reply_text("Игра не найдена.")
            return
        is_drawn = row[0]
        if is_drawn:
            await update.message.reply_text("Нельзя выйти — жеребьёвка уже проведена.")
            return
        await db.execute("DELETE FROM participants WHERE game_code = ? AND tg_id = ?", (code, tg_id))
        await db.commit()
    await update.message.reply_text(f"Вы вышли из игры {code}.")

async def status_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /status <КОД>")
        return
    code = context.args[0].upper()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT title, organizer_id, draw_date, min_participants, is_drawn FROM games WHERE code = ?", (code,))
        game = await cur.fetchone()
        if not game:
            await update.message.reply_text("Игра не найдена.")
            return
        title, org, draw_date, min_p, is_drawn = game
        cur = await db.execute("SELECT u.tg_id, u.first_name, p.fio FROM participants part JOIN users u ON part.tg_id = u.tg_id LEFT JOIN profiles p ON p.tg_id = u.tg_id WHERE part.game_code = ?", (code,))
        rows = await cur.fetchall()
        participants = [f"{r[0]} — {r[1]} / {r[2] or '-'}" for r in rows]
    text = f"Игра {code}: {title}\nОрганизатор: {org}\nДата жеребьёвки: {draw_date}\nМинимум участников: {min_p}\nЖеребьёвка проведена: {'Да' if is_drawn else 'Нет'}\n\nУчастники:\n" + ("\n".join(participants) if participants else "Пока нет")
    await update.message.reply_text(text)

# ---------- Mixing / assignment ----------
async def generate_derangement(lst):
    # try to produce a derangement (no element at same index)
    # simple retry shuffle method with limited attempts
    n = len(lst)
    if n == 1:
        return None
    attempts = 0
    while attempts < 2000:
        attempt = lst[:]
        random.shuffle(attempt)
        if all(a != b for a, b in zip(lst, attempt)):
            return attempt
        attempts += 1
    return None

async def mix_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /mix <КОД>")
        return
    code = context.args[0].upper()
    tg_id = update.effective_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        # check organizer
        cur = await db.execute("SELECT organizer_id, min_participants, is_drawn FROM games WHERE code = ?", (code,))
        row = await cur.fetchone()
        if not row:
            await update.message.reply_text("Игра не найдена.")
            return
        organizer_id, min_p, is_drawn = row
        if organizer_id != tg_id:
            await update.message.reply_text("Только организатор может запускать жеребьёвку.")
            return
        if is_drawn:
            await update.message.reply_text("Жеребьёвка уже проведена.")
            return
        cur = await db.execute("SELECT tg_id FROM participants WHERE game_code = ?", (code,))
        rows = await cur.fetchall()
        p_ids = [r[0] for r in rows]
        if len(p_ids) < min_p:
            await update.message.reply_text(f"Недостаточно участников (нужно минимум {min_p}).")
            return
        # create derangement
        recipients = await generate_derangement(p_ids)
        if recipients is None:
            await update.message.reply_text("Не удалось сгенерировать корректное распределение. Попробуйте снова.")
            return
        # store assignments
        await db.executemany("INSERT INTO assignments (game_code, santa_id, recipient_id) VALUES (?, ?, ?)",
[(code, santa, recipient) for santa, recipient in zip(p_ids, recipients)])
        await db.execute("UPDATE games SET is_drawn = 1 WHERE code = ?", (code,))
        await db.commit()

        # notify each santa privately
        for santa, recipient in zip(p_ids, recipients):
            # fetch recipient info, wishlist
            cur = await db.execute("SELECT p.fio, p.bio, u.first_name FROM users u LEFT JOIN profiles p ON p.tg_id = u.tg_id WHERE u.tg_id = ?", (recipient,))
            rinfo = await cur.fetchone()
            fio = rinfo[0] or rinfo[2] or "—"
            bio = rinfo[1] or "—"
            # fetch wishlist items
            cur = await db.execute("SELECT title, description, photo_file_id FROM wishlist_items WHERE tg_id = ?", (recipient,))
            items = await cur.fetchall()
            wl_text = ""
            for it in items:
                wl_text += f"- {it[0]}: {it[1]}\n"
            msg = f"Вы — Санта!\nВаш получатель: {fio}\nБиография: {bio}\nВишлист:\n{wl_text or 'вишлист пуст'}"
            try:
                await context.bot.send_message(chat_id=santa, text=msg)
                # send photos separately if any
                for it in items:
                    if it[2]:
                        await context.bot.send_photo(chat_id=santa, photo=it[2], caption=it[0])
            except Exception as e:
                logger.warning("Не удалось отправить сообщение пользователю %s: %s", santa, e)
    await update.message.reply_text("Жеребьёвка проведена и результаты отправлены каждому участнику в личные сообщения.")

# ---------- My recipient ----------
async def my_recipient(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /my_recipient <КОД>")
        return
    code = context.args[0].upper()
    tg_id = update.effective_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT recipient_id FROM assignments WHERE game_code = ? AND santa_id = ?", (code, tg_id))
        row = await cur.fetchone()
        if not row:
            await update.message.reply_text("Информация не найдена. Возможно жеребьёвка ещё не проведена или вы не участник.")
            return
        recipient = row[0]
        cur = await db.execute("SELECT p.fio, p.bio FROM profiles p WHERE p.tg_id = ?", (recipient,))
        prof = await cur.fetchone()
        fio = prof[0] if prof else None
        bio = prof[1] if prof else None
        # wishlist items
        cur = await db.execute("SELECT title, description, photo_file_id FROM wishlist_items WHERE tg_id = ?", (recipient,))
        items = await cur.fetchall()
    text = f"Получатель: {fio or '—'}\nБиография: {bio or '—'}\nВишлист:\n"
    for it in items:
        text += f"- {it[0]}: {it[1]}\n"
    await update.message.reply_text(text)
    for it in items:
        if it[2]:
            await update.message.reply_photo(chat_id=update.effective_user.id, photo=it[2], caption=it[0])

# ---------- Anonymous questions ----------
async def ask_anonymous(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # /ask <КОД> <текст>
    if len(context.args) < 2:
        await update.message.reply_text("Использование: /ask <КОД> <сообщение>")
        return
    code = context.args[0].upper()
    message_text = " ".join(context.args[1:])
    tg_id = update.effective_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT recipient_id FROM assignments WHERE game_code = ? AND santa_id = ?", (code, tg_id))
        row = await cur.fetchone()
        if not row:
            await update.message.reply_text("Информация не найдена. Возможно жеребьёвка ещё не проведена или вы не участник.")
            return
        recipient = row[0]
        # forward anon message to recipient
        try:
            await context.bot.send_message(chat_id=recipient, text=f"🔒 Анонимный вопрос от вашего Санты:\n\n{message_text}")
            await update.message.reply_text("Анонимное сообщение отправлено.")
except Exception as e:
            logger.warning("Ошибка при отправке анонимного сообщения: %s", e)
            await update.message.reply_text("Не удалось отправить сообщение получателю. Возможно он запретил сообщения от бота.")

# ---------- Startup ----------
async def main():
    await init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # basic commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("create_game", create_game))
    app.add_handler(CommandHandler("join", join_game))
    app.add_handler(CommandHandler("leave", leave_game))
    app.add_handler(CommandHandler("status", status_game))
    app.add_handler(CommandHandler("mix", mix_game))
    app.add_handler(CommandHandler("send", mix_game))  # alias
    app.add_handler(CommandHandler("my_recipient", my_recipient))
    app.add_handler(CommandHandler("ask", ask_anonymous))
    # wishlist commands
    app.add_handler(CommandHandler("wishlist", wishlist))
    app.add_handler(CommandHandler("wl_list", wl_list))
    app.add_handler(CommandHandler("wl_clear", wl_clear))
    # flows
    profile_conv = ConversationHandler(
        entry_points=[CommandHandler('profile', profile)],
        states={
            PROFILE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, profile_name)],
            PROFILE_BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, profile_bio)],
        },
        fallbacks=[CommandHandler('cancel', cancel_profile)],
    )
    app.add_handler(profile_conv)

    wl_conv = ConversationHandler(
        entry_points=[CommandHandler('wl_add', wl_add_start)],
        states={
            WL_ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, wl_add_name)],
            WL_ADD_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, wl_add_desc)],
            WL_ADD_PHOTO: [
                MessageHandler(filters.PHOTO, wl_add_photo),
                CommandHandler('skip', wl_skip_photo)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel_profile)],
    )
    app.add_handler(wl_conv)

    # simple handlers for wl_add convenience
    app.add_handler(CommandHandler("wl_add", wl_add_start))

    # start
    logger.info("Запуск бота")
    await app.start()
    await app.updater.start_polling()  # starts polling
    await app.idle()

if name == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен")