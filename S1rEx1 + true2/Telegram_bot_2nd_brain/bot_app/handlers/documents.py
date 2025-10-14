"""Handlers for document processing."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import database as db_module
from document_processor import DocumentProcessor
from openrouter_client import openrouter_client


class DocumentHandlers:
    """Handle incoming documents and photos."""

    async def start_extract_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query

        await query.edit_message_text(
            "📄 **Извлечение информации**\n\n"
            "Отправьте фото или PDF документ для обработки.\n"
            "Я извлеку текст и создам краткое содержание.\n\n"
            "Для отмены напишите /cancel",
            parse_mode="Markdown",
        )

        return self.MAIN_MENU

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id

        if update.message.photo:
            file = await update.message.photo[-1].get_file()
            file_bytes = await file.download_as_bytearray()
            file_type = 'image'
        elif update.message.document:
            document = update.message.document
            if document.mime_type == 'application/pdf':
                file = await document.get_file()
                file_bytes = await file.download_as_bytearray()
                file_type = 'pdf'
            else:
                await update.message.reply_text("⚠️ Поддерживаются только PDF документы и изображения.")
                return
        else:
            return

        processing_msg = await update.message.reply_text("⏳ Обрабатываю документ...")

        try:
            result = await DocumentProcessor.process_file(file_bytes, file_type)

            if result['success']:
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

                async with db_module.AsyncSessionLocal() as session:
                    db = self.db_manager_class(session)
                    user = await db.get_or_create_user(telegram_id=user_id)
                    user.total_messages += 1
                    await session.commit()

                await processing_msg.edit_text(response, parse_mode="Markdown")

                keyboard = [
                    [InlineKeyboardButton("💾 Сохранить как конспект", callback_data="save_as_note")],
                    [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")],
                ]

                await update.message.reply_text(
                    "Хотите сохранить это как конспект?",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )

                context.user_data['extracted_text'] = result['text']
                context.user_data['extracted_summary'] = ai_summary
            else:
                await processing_msg.edit_text(
                    f"❌ Ошибка обработки документа: {result.get('error', 'Неизвестная ошибка')}"
                )

        except Exception as exc:
            self.logger.error("Error processing document: %s", exc)
            await processing_msg.edit_text("❌ Произошла ошибка при обработке документа.")
