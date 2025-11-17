"""Handlers for unified note creation workflow."""

from __future__ import annotations

from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from config import config
from document_processor import DocumentProcessor
from openrouter_client import openrouter_client

from ..responses import notes as notes_responses
from ..services import db_session


class NotesHandlers:
    """Create notes from text messages or files."""

    async def start_note_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query

        await query.edit_message_text(
            notes_responses.note_creation_intro(),
            parse_mode="Markdown",
        )

        return self.NOTE_MATERIAL

    async def handle_note_material(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        message = update.message
        if not message:
            return self.NOTE_MATERIAL

        if message.document or message.photo:
            return await self._handle_file_material(update, context)

        if message.text:
            return await self._handle_text_material(update, context)

        await message.reply_text(
            notes_responses.unsupported_material_message(),
            reply_markup=self.get_back_keyboard(),
        )
        return self.NOTE_MATERIAL

    async def _handle_text_material(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        message = update.message
        assert message is not None

        user_id = update.effective_user.id
        content = message.text or ""

        async with db_session(self.db_manager_class) as (_, db):
            user = await db.get_or_create_user(telegram_id=user_id)
            user_model = user.preferred_model or config.model_name

        summary = await openrouter_client.generate_summary(content, model=user_model)
        topic = self._derive_topic(summary)

        async with db_session(self.db_manager_class) as (_, db):
            await db.create_note(
                user_id=user.id,
                topic=topic,
                content=content,
                summary=summary,
            )

        await message.reply_text(
            notes_responses.note_saved_message(topic, summary),
            reply_markup=self.get_back_keyboard(),
            parse_mode="Markdown",
        )

        return self.MAIN_MENU

    async def _handle_file_material(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        message = update.message
        assert message is not None  # for type checkers

        user_id = update.effective_user.id

        if message.photo:
            file = await message.photo[-1].get_file()
            file_bytes = await file.download_as_bytearray()
            file_type = "image"
        elif message.document:
            document = message.document
            if document.mime_type != "application/pdf":
                await message.reply_text(
                    notes_responses.unsupported_material_message(),
                    reply_markup=self.get_back_keyboard(),
                )
                return self.NOTE_MATERIAL
            file = await document.get_file()
            file_bytes = await file.download_as_bytearray()
            file_type = "pdf"
        else:
            await message.reply_text(
                notes_responses.unsupported_material_message(),
                reply_markup=self.get_back_keyboard(),
            )
            return self.NOTE_MATERIAL

        processing_msg = await message.reply_text(notes_responses.note_processing_message())

        try:
            result = await DocumentProcessor.process_file(file_bytes, file_type)

            if not result.get("success"):
                await processing_msg.edit_text(
                    notes_responses.note_error_message(result.get("error", "Неизвестная ошибка")),
                    reply_markup=self.get_back_keyboard(),
                )
                return self.NOTE_MATERIAL

            extracted_text = result.get("text", "")

            async with db_session(self.db_manager_class) as (session, db):
                user = await db.get_or_create_user(telegram_id=user_id)
                user_model = user.preferred_model or config.model_name

            summary = await openrouter_client.generate_summary(
                extracted_text[:2000] or extracted_text,
                model=user_model
            )

            topic = self._derive_topic(
                summary,
                fallback=result.get("metadata", {}).get("title"),
            )
            key_points = (result.get("key_points") or [])[:5]

            async with db_session(self.db_manager_class) as (session, db):
                await db.create_note(
                    user_id=user.id,
                    topic=topic,
                    content=extracted_text,
                    summary=summary,
                )

                user.total_messages += 1
                await session.commit()

            await processing_msg.edit_text(
                notes_responses.note_saved_message(topic, summary, key_points),
                parse_mode="Markdown",
                reply_markup=self.get_back_keyboard(),
            )

            return self.MAIN_MENU

        except Exception as exc:  # pragma: no cover - defensive logging
            self.logger.error("Error processing material: %s", exc)
            await processing_msg.edit_text(
                notes_responses.note_error_message(),
                reply_markup=self.get_back_keyboard(),
            )
            return self.NOTE_MATERIAL

    @staticmethod
    def _derive_topic(summary: str, fallback: str | None = None) -> str:
        if fallback:
            return fallback

        first_line = summary.strip().splitlines()[0] if summary else ""
        topic = first_line[:80] if first_line else "Материал"
        return topic or datetime.utcnow().strftime("Материал %Y-%m-%d %H:%M")
