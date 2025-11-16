"""General handlers shared across modes."""
from telegram import Update
from telegram.ext import ContextTypes

from config import config
from openrouter_client import openrouter_client
from prompts import GENERAL_ASSISTANT_PROMPT

from ..responses import general as general_responses
from ..services import db_session


class GeneralHandlers:
    """General conversation and fallback handlers."""

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        message_text = update.message.text

        async with db_session(self.db_manager_class) as (session, db):
            user = await db.get_or_create_user(telegram_id=user_id)

            conversation_id = context.user_data.get('conversation_id')
            if not conversation_id:
                conversation = await db.create_conversation(user.id, 'general')
                conversation_id = conversation.id
                context.user_data['conversation_id'] = conversation_id

            await db.add_message(
                conversation_id=conversation_id,
                role='user',
                content=message_text,
            )

            messages = await db.get_conversation_history(
                conversation_id,
                limit=config.max_context_messages,
            )

            ai_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

            system_prompt = user.custom_prompt or GENERAL_ASSISTANT_PROMPT
            if user.specific_instructions:
                system_prompt += f"\n\n{user.specific_instructions}"

            response_text, tokens_used = await openrouter_client.generate_response(
                messages=ai_messages,
                system_prompt=system_prompt,
                max_tokens=user.max_tokens,
                temperature=user.temperature,
            )

            await db.add_message(
                conversation_id=conversation_id,
                role='assistant',
                content=response_text,
                tokens_used=tokens_used,
            )

            user.total_messages += 1
            user.total_tokens_used += tokens_used
            await session.commit()

        await update.message.reply_text(response_text, parse_mode="Markdown")

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text(
            general_responses.cancel_message(),
            reply_markup=self.get_back_keyboard(),
        )
        return self.MAIN_MENU

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.logger.error("Update %s caused error %s", update, context.error)

        try:
            if update and getattr(update, "effective_message", None):
                await update.effective_message.reply_text(
                    general_responses.error_message()
                )
        except Exception:
            pass
