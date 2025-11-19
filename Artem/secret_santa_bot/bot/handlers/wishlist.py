"""Обработчики вишлиста."""
from telebot import types
from telebot.apihelper import ApiTelegramException

from bot.bot import bot, send_wishlist_menu
from database import operations
from utils.helpers import log_action, send_wishlist_view, set_step, build_wishlist_view

def start_add_item_flow(message: types.Message) -> None:
    operations.ensure_user(message.from_user.id, message.from_user.username)
    set_step(message.from_user.id, "wish_description", {})
    log_action("start_add_item", user_id=message.from_user.id)
    bot.send_message(message.chat.id, "💝 Опишите подарок, который хотите получить:")

def prompt_wishlist_deletion(message: types.Message) -> None:
    operations.ensure_user(message.from_user.id, message.from_user.username)
    log_action("prompt_remove_item", user_id=message.from_user.id)
    send_wishlist_view(message.chat.id, message.from_user.id)

@bot.message_handler(commands=["wishlist"])
def cmd_wishlist(message: types.Message) -> None:
    operations.ensure_user(message.from_user.id, message.from_user.username)
    log_action("command_wishlist", user_id=message.from_user.id)
    send_wishlist_view(message.chat.id, message.from_user.id)

@bot.message_handler(commands=["add_item"])
def cmd_add_item(message: types.Message) -> None:
    start_add_item_flow(message)

@bot.message_handler(commands=["remove_item"])
def cmd_remove_item(message: types.Message) -> None:
    operations.ensure_user(message.from_user.id, message.from_user.username)
    log_action("command_remove_item", user_id=message.from_user.id, payload=message.text)
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        prompt_wishlist_deletion(message)
        return
    removed = operations.delete_wish_item(message.from_user.id, int(parts[1]))
    log_action("remove_item_result", user_id=message.from_user.id, item_id=parts[1], removed=removed)
    bot.send_message(message.chat.id, "✅ Подарок удалён." if removed else "❌ Пункт не найден.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_wish:"))
def cb_delete_wish(call: types.CallbackQuery) -> None:
    try:
        item_id = int(call.data.split(":", 1)[1])
    except (ValueError, IndexError):
        log_action("callback_delete_wish_invalid", user_id=call.from_user.id, data=call.data)
        bot.answer_callback_query(call.id, "❌ Некорректный выбор.", show_alert=True)
        return
    
    if not operations.delete_wish_item(call.from_user.id, item_id):
        log_action("callback_delete_wish_missing", user_id=call.from_user.id, item_id=item_id)
        bot.answer_callback_query(call.id, "❌ Подарок не найден.", show_alert=True)
        return
    
    log_action("callback_delete_wish", user_id=call.from_user.id, item_id=item_id)
    text, markup = build_wishlist_view(call.from_user.id)
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML",
        )
    except ApiTelegramException:
        bot.send_message(call.message.chat.id, text, reply_markup=markup)
    
    bot.answer_callback_query(call.id, "✅ Удалено")