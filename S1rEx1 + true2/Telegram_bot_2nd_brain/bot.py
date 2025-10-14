"""
Main Telegram bot implementation
"""
import os
import logging
import asyncio
from datetime import datetime
from typing import Optional
from html import escape

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes
)

from config import config, validate_config
from database import init_database, DatabaseManager
import database as db_module
from prompts import GENERAL_ASSISTANT_PROMPT
from openrouter_client import openrouter_client
from document_processor import DocumentProcessor

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, config.log_level)
)
logger = logging.getLogger(__name__)

# Conversation states
(MAIN_MENU, PROFILE_MENU, NOTES_TOPIC, NOTES_CONTENT, 
 INSTRUCTOR_TOPIC, INSTRUCTOR_QUESTION, PROMPT_SETTING,
 INSTRUCTIONS_SETTING) = range(8)

# User context storage (in production, consider using Redis)
user_contexts = {}


class TelegramBot:
    """Main Telegram bot class"""
    
    def __init__(self):
        """Initialize the bot"""
        self.app = None
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle /start command"""
        user = update.effective_user
        logger.info(f"User {user.id} started the bot")
        
        # Save user to database
        async with db_module.AsyncSessionLocal() as session:
            db = DatabaseManager(session)
            await db.get_or_create_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
        
        # Create main menu keyboard
        keyboard = [
            [InlineKeyboardButton("👤 Профиль", callback_data="profile")],
            [InlineKeyboardButton("📝 Ведение конспектов", callback_data="notes")],
            [InlineKeyboardButton("📄 Выжимка с фото/PDF", callback_data="extract")],
            [InlineKeyboardButton("👨‍🏫 Инструктор", callback_data="instructor")],
            [InlineKeyboardButton("🔍 Поиск", callback_data="search")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = (
            f"👋 Привет, {user.first_name}!\n\n"
            "Я - образовательный бот с AI от DeepSeek V3.\n"
            "Выберите режим работы:"
        )
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
        return MAIN_MENU
    
    async def main_menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle main menu selections"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "back_to_main":
            return await self.back_to_main_menu(update, context)

        if query.data == "profile":
            return await self.show_profile_menu(update, context)
        elif query.data == "notes":
            return await self.start_notes_mode(update, context)
        elif query.data == "extract":
            return await self.start_extract_mode(update, context)
        elif query.data == "instructor":
            return await self.start_instructor_mode(update, context)
        elif query.data == "search":
            return await self.start_search_mode(update, context)
        
        return MAIN_MENU
    
    async def show_profile_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show profile menu"""
        query = update.callback_query
        user_id = update.effective_user.id
        
        # Get user data
        async with db_module.AsyncSessionLocal() as session:
            db = DatabaseManager(session)
            user = await db.get_or_create_user(telegram_id=user_id)
            stats = await db.get_user_statistics(user.id)
        
        keyboard = [
            [InlineKeyboardButton("⚙️ Настройка промпта", callback_data="set_prompt")],
            [InlineKeyboardButton("📋 Специфические инструкции", callback_data="set_instructions")],
            [InlineKeyboardButton("👁 Показать текущие настройки", callback_data="show_settings")],
            [InlineKeyboardButton("📊 Статистика", callback_data="show_stats")],
            [InlineKeyboardButton("ℹ️ Информация о пользователе", callback_data="user_info")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "👤 **Профиль**\n\nВыберите действие:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return PROFILE_MENU
    
    async def profile_menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle profile menu selections"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "back_to_main":
            return await self.back_to_main_menu(update, context)

        if query.data == "profile":
            return await self.show_profile_menu(update, context)

        if query.data == "set_prompt":
            await query.edit_message_text(
                "⚙️ **Настройка промпта**\n\n"
                "Отправьте новый системный промпт для AI.\n"
                "Это повлияет на стиль и поведение ответов.\n\n"
                "Для отмены напишите /cancel",
                parse_mode="Markdown"
            )
            return PROMPT_SETTING
        
        elif query.data == "set_instructions":
            await query.edit_message_text(
                "📋 **Специфические инструкции**\n\n"
                "Отправьте дополнительные инструкции для AI.\n"
                "Например: 'Отвечай кратко', 'Используй примеры', и т.д.\n\n"
                "Для отмены напишите /cancel",
                parse_mode="Markdown"
            )
            return INSTRUCTIONS_SETTING
        
        elif query.data == "show_settings":
            return await self.show_current_settings(update, context)
        
        elif query.data == "show_stats":
            return await self.show_statistics(update, context)
        
        elif query.data == "user_info":
            return await self.show_user_info(update, context)
        
        elif query.data == "back_to_main":
            return await self.back_to_main_menu(update, context)
        
        return PROFILE_MENU
    
    async def set_prompt(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Set custom prompt"""
        user_id = update.effective_user.id
        new_prompt = update.message.text
        
        async with db_module.AsyncSessionLocal() as session:
            db = DatabaseManager(session)
            await db.update_user_profile(
                telegram_id=user_id,
                custom_prompt=new_prompt
            )
        
        await update.message.reply_text(
            "✅ Промпт успешно обновлен!",
            reply_markup=self.get_back_keyboard()
        )
        
        return MAIN_MENU
    
    async def set_instructions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Set specific instructions"""
        user_id = update.effective_user.id
        new_instructions = update.message.text
        
        async with db_module.AsyncSessionLocal() as session:
            db = DatabaseManager(session)
            await db.update_user_profile(
                telegram_id=user_id,
                specific_instructions=new_instructions
            )
        
        await update.message.reply_text(
            "✅ Инструкции успешно обновлены!",
            reply_markup=self.get_back_keyboard()
        )
        
        return MAIN_MENU
    
    async def show_current_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show current user settings"""
        query = update.callback_query
        user_id = update.effective_user.id
        
        async with db_module.AsyncSessionLocal() as session:
            db = DatabaseManager(session)
            user = await db.get_or_create_user(telegram_id=user_id)
        
        settings_text = (
            "👁 **Текущие настройки**\n\n"
            f"**Промпт:** {user.custom_prompt or 'Стандартный'}\n\n"
            f"**Инструкции:** {user.specific_instructions or 'Не заданы'}\n\n"
            f"**Max токенов:** {user.max_tokens}\n"
            f"**Temperature:** {user.temperature}"
        )
        
        await query.edit_message_text(
            settings_text,
            reply_markup=self.get_back_to_profile_keyboard(),
            parse_mode="Markdown"
        )
        
        return PROFILE_MENU
    
    async def show_statistics(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show user statistics"""
        query = update.callback_query
        user_id = update.effective_user.id
        
        async with db_module.AsyncSessionLocal() as session:
            db = DatabaseManager(session)
            user = await db.get_or_create_user(telegram_id=user_id)
            stats = await db.get_user_statistics(user.id)
        
        stats_text = (
            "📊 **Статистика использования**\n\n"
            f"**Всего сообщений:** {stats.get('total_messages', 0)}\n"
            f"**Токенов использовано:** {stats.get('total_tokens_used', 0)}\n"
            f"**Конспектов создано:** {stats.get('notes_count', 0)}\n"
            f"**Диалогов:** {stats.get('conversations_count', 0)}\n"
            f"**Зарегистрирован:** {stats.get('member_since', 'Неизвестно')}\n"
            f"**Последняя активность:** {stats.get('last_active', 'Неизвестно')}"
        )
        
        await query.edit_message_text(
            stats_text,
            reply_markup=self.get_back_to_profile_keyboard(),
            parse_mode="Markdown"
        )
        
        return PROFILE_MENU
    
    async def show_user_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show user information"""
        query = update.callback_query
        user = update.effective_user
        
        info_text = (
            "ℹ️ <b>Информация о пользователе</b>\n\n"
            f"<b>ID:</b> {escape(str(user.id))}\n"
            f"<b>Имя:</b> {escape(user.first_name or 'Не указано')}\n"
            f"<b>Фамилия:</b> {escape(user.last_name or 'Не указана')}\n"
            f"<b>Username:</b> @{escape(user.username) if user.username else 'Не указан'}\n"
            f"<b>Язык:</b> {escape(user.language_code or 'Не определен')}"
        )

        await query.edit_message_text(
            info_text,
            reply_markup=self.get_back_to_profile_keyboard(),
            parse_mode="HTML"
        )
        
        return PROFILE_MENU
    
    async def start_notes_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start notes mode"""
        query = update.callback_query
        
        await query.edit_message_text(
            "📝 **Режим конспектов**\n\n"
            "Введите тему конспекта:",
            parse_mode="Markdown"
        )
        
        return NOTES_TOPIC
    
    async def handle_notes_topic(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle notes topic input"""
        topic = update.message.text
        context.user_data['notes_topic'] = topic
        
        await update.message.reply_text(
            f"📝 Тема: **{topic}**\n\n"
            "Теперь отправьте содержание конспекта:",
            parse_mode="Markdown"
        )
        
        return NOTES_CONTENT
    
    async def handle_notes_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle notes content and save"""
        content = update.message.text
        topic = context.user_data.get('notes_topic', 'Без темы')
        user_id = update.effective_user.id
        
        # Generate summary using AI
        summary = await openrouter_client.generate_summary(content)
        
        # Save to database
        async with db_module.AsyncSessionLocal() as session:
            db = DatabaseManager(session)
            user = await db.get_or_create_user(telegram_id=user_id)
            note = await db.create_note(
                user_id=user.id,
                topic=topic,
                content=content,
                summary=summary
            )
        
        await update.message.reply_text(
            f"✅ Конспект сохранен!\n\n"
            f"**Тема:** {topic}\n"
            f"**Краткое содержание:** {summary[:200]}...",
            reply_markup=self.get_back_keyboard(),
            parse_mode="Markdown"
        )
        
        return MAIN_MENU
    
    async def start_extract_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start document extraction mode"""
        query = update.callback_query
        
        await query.edit_message_text(
            "📄 **Извлечение информации**\n\n"
            "Отправьте фото или PDF документ для обработки.\n"
            "Я извлеку текст и создам краткое содержание.\n\n"
            "Для отмены напишите /cancel",
            parse_mode="Markdown"
        )
        
        return MAIN_MENU
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle document upload"""
        user_id = update.effective_user.id
        
        # Check if it's a photo or document
        if update.message.photo:
            # Handle photo
            file = await update.message.photo[-1].get_file()
            file_bytes = await file.download_as_bytearray()
            file_type = 'image'
        elif update.message.document:
            # Handle document
            document = update.message.document
            if document.mime_type == 'application/pdf':
                file = await document.get_file()
                file_bytes = await file.download_as_bytearray()
                file_type = 'pdf'
            else:
                await update.message.reply_text(
                    "⚠️ Поддерживаются только PDF документы и изображения."
                )
                return
        else:
            return
        
        # Send processing message
        processing_msg = await update.message.reply_text("⏳ Обрабатываю документ...")
        
        try:
            # Process the document
            result = await DocumentProcessor.process_file(file_bytes, file_type)
            
            if result['success']:
                # Use AI to create a better summary
                ai_summary = await openrouter_client.generate_summary(result['text'][:2000])
                
                response = (
                    "✅ **Документ обработан**\n\n"
                    f"**Тип:** {result['metadata'].get('type', 'Неизвестно')}\n"
                )
                
                if result['metadata'].get('page_count'):
                    response += f"**Страниц:** {result['metadata']['page_count']}\n"
                
                response += f"\n**Краткое содержание:**\n{ai_summary[:500]}\n\n"
                
                if result['key_points']:
                    response += "**Ключевые пункты:**\n"
                    for i, point in enumerate(result['key_points'][:5], 1):
                        response += f"{i}. {point[:100]}\n"
                
                # Save to database
                async with db_module.AsyncSessionLocal() as session:
                    db = DatabaseManager(session)
                    user = await db.get_or_create_user(telegram_id=user_id)
                    
                    # Update statistics
                    user.total_messages += 1
                    await session.commit()
                
                await processing_msg.edit_text(response, parse_mode="Markdown")
                
                # Ask if user wants to save as note
                keyboard = [
                    [InlineKeyboardButton("💾 Сохранить как конспект", callback_data="save_as_note")],
                    [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "Хотите сохранить это как конспект?",
                    reply_markup=reply_markup
                )
                
                # Store extracted text in context for later use
                context.user_data['extracted_text'] = result['text']
                context.user_data['extracted_summary'] = ai_summary
                
            else:
                await processing_msg.edit_text(
                    f"❌ Ошибка обработки документа: {result.get('error', 'Неизвестная ошибка')}"
                )
                
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            await processing_msg.edit_text(
                "❌ Произошла ошибка при обработке документа."
            )
    
    async def start_instructor_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start instructor mode"""
        query = update.callback_query
        
        await query.edit_message_text(
            "👨‍🏫 **Режим Инструктора**\n\n"
            "Введите тему, которую хотите изучить:",
            parse_mode="Markdown"
        )
        
        return INSTRUCTOR_TOPIC
    
    async def handle_instructor_topic(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle instructor topic"""
        topic = update.message.text
        context.user_data['instructor_topic'] = topic
        
        keyboard = [
            [KeyboardButton("Начальный")],
            [KeyboardButton("Средний")],
            [KeyboardButton("Продвинутый")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        
        await update.message.reply_text(
            f"📚 Тема: **{topic}**\n\n"
            "Выберите уровень сложности:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return INSTRUCTOR_QUESTION
    
    async def handle_instructor_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle instructor question and generate response"""
        user_id = update.effective_user.id
        text = update.message.text
        
        # Check if it's a level selection or a question
        if text in ["Начальный", "Средний", "Продвинутый"]:
            level_map = {
                "Начальный": "beginner",
                "Средний": "intermediate",
                "Продвинутый": "advanced"
            }
            context.user_data['instructor_level'] = level_map[text]
            
            await update.message.reply_text(
                "Отлично! Теперь задайте ваш вопрос по теме:",
                reply_markup=ReplyKeyboardRemove()
            )
            return INSTRUCTOR_QUESTION
        
        # It's a question - generate response
        topic = context.user_data.get('instructor_topic', 'General')
        level = context.user_data.get('instructor_level', 'intermediate')
        
        # Get user's custom instructions
        async with db_module.AsyncSessionLocal() as session:
            db = DatabaseManager(session)
            user = await db.get_or_create_user(telegram_id=user_id)
            custom_instructions = user.specific_instructions
        
        # Send typing action
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Generate educational response
        response = await openrouter_client.instructor_mode(
            topic=topic,
            question=text,
            level=level,
            custom_instructions=custom_instructions
        )
        
        # Send response
        await update.message.reply_text(
            response,
            parse_mode="Markdown"
        )
        
        # Ask for next action
        keyboard = [
            [InlineKeyboardButton("❓ Задать еще вопрос", callback_data="more_instructor")],
            [InlineKeyboardButton("🔄 Сменить тему", callback_data="instructor")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Что дальше?",
            reply_markup=reply_markup
        )
        
        return MAIN_MENU
    
    async def start_search_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start search mode"""
        query = update.callback_query
        user_id = update.effective_user.id
        
        # Get user's notes for searching
        async with db_module.AsyncSessionLocal() as session:
            db = DatabaseManager(session)
            user = await db.get_or_create_user(telegram_id=user_id)
            notes = await db.get_user_notes(user.id)
        
        if not notes:
            await query.edit_message_text(
                "📭 У вас пока нет сохраненных конспектов для поиска.\n"
                "Сначала создайте несколько конспектов!",
                reply_markup=self.get_back_keyboard(),
                parse_mode="Markdown"
            )
            return MAIN_MENU
        
        # Show available topics
        topics = list(set(note.topic for note in notes))
        keyboard = []
        for topic in topics[:10]:  # Limit to 10 topics
            keyboard.append([InlineKeyboardButton(topic, callback_data=f"search_topic_{topic[:20]}")])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🔍 **Поиск по конспектам**\n\n"
            "Выберите тему для поиска:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return MAIN_MENU
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle general messages"""
        user_id = update.effective_user.id
        message_text = update.message.text
        
        # Get user settings
        async with db_module.AsyncSessionLocal() as session:
            db = DatabaseManager(session)
            user = await db.get_or_create_user(telegram_id=user_id)
            
            # Create or get conversation
            if 'conversation_id' not in context.user_data:
                conversation = await db.create_conversation(user.id, 'general')
                context.user_data['conversation_id'] = conversation.id
            
            # Add user message to history
            await db.add_message(
                conversation_id=context.user_data['conversation_id'],
                role='user',
                content=message_text
            )
            
            # Get conversation history
            messages = await db.get_conversation_history(
                context.user_data['conversation_id'],
                limit=config.max_context_messages
            )
            
            # Format messages for AI
            ai_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            # Send typing action
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            
            # Generate response
            system_prompt = user.custom_prompt or GENERAL_ASSISTANT_PROMPT
            if user.specific_instructions:
                system_prompt += f"\n\n{user.specific_instructions}"
            
            response_text, tokens_used = await openrouter_client.generate_response(
                messages=ai_messages,
                system_prompt=system_prompt,
                max_tokens=user.max_tokens,
                temperature=user.temperature
            )
            
            # Save assistant response
            await db.add_message(
                conversation_id=context.user_data['conversation_id'],
                role='assistant',
                content=response_text,
                tokens_used=tokens_used
            )
            
            # Update user statistics
            user.total_messages += 1
            user.total_tokens_used += tokens_used
            await session.commit()
        
        # Send response
        await update.message.reply_text(response_text, parse_mode="Markdown")
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel current operation"""
        await update.message.reply_text(
            "❌ Операция отменена.",
            reply_markup=self.get_back_keyboard()
        )
        return MAIN_MENU
    
    async def back_to_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Return to main menu"""
        query = update.callback_query
        
        keyboard = [
            [InlineKeyboardButton("👤 Профиль", callback_data="profile")],
            [InlineKeyboardButton("📝 Ведение конспектов", callback_data="notes")],
            [InlineKeyboardButton("📄 Выжимка с фото/PDF", callback_data="extract")],
            [InlineKeyboardButton("👨‍🏫 Инструктор", callback_data="instructor")],
            [InlineKeyboardButton("🔍 Поиск", callback_data="search")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🏠 **Главное меню**\n\nВыберите режим работы:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return MAIN_MENU
    
    def get_back_keyboard(self):
        """Get back to main menu keyboard"""
        keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]]
        return InlineKeyboardMarkup(keyboard)
    
    def get_back_to_profile_keyboard(self):
        """Get back to profile keyboard"""
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="profile")]]
        return InlineKeyboardMarkup(keyboard)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")
        
        try:
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "❌ Произошла ошибка при обработке вашего запроса. "
                    "Пожалуйста, попробуйте еще раз или напишите /start для перезапуска."
                )
        except:
            pass
    
    def setup_handlers(self):
        """Setup bot handlers"""
        # Conversation handler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={
                MAIN_MENU: [
                    CallbackQueryHandler(self.main_menu_callback),
                    MessageHandler(filters.Document.PDF | filters.PHOTO, self.handle_document),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message),
                ],
                PROFILE_MENU: [
                    CallbackQueryHandler(self.profile_menu_callback),
                ],
                NOTES_TOPIC: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_notes_topic),
                ],
                NOTES_CONTENT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_notes_content),
                ],
                INSTRUCTOR_TOPIC: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_instructor_topic),
                ],
                INSTRUCTOR_QUESTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_instructor_question),
                ],
                PROMPT_SETTING: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_prompt),
                ],
                INSTRUCTIONS_SETTING: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_instructions),
                ],
            },
            fallbacks=[
                CommandHandler("cancel", self.cancel),
                CallbackQueryHandler(self.back_to_main_menu, pattern="^back_to_main$"),
            ],
        )
        
        self.app.add_handler(conv_handler)
        
        # Error handler
        self.app.add_error_handler(self.error_handler)
    
    async def post_init(self, application: Application) -> None:
        """Initialize after application is created"""
        await init_database()
        logger.info("Database initialized")
    
    def run(self):
        """Run the bot"""
        # Validate configuration
        if not validate_config():
            return
        
        # Create application
        self.app = Application.builder().token(config.telegram_token).post_init(self.post_init).build()
        
        # Setup handlers
        self.setup_handlers()
        
        # Start bot
        logger.info("Starting bot...")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()
