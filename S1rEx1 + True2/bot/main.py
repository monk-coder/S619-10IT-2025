from __future__ import annotations

import asyncio
import io
import logging
from datetime import datetime
from typing import Iterable

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import get_settings
from database import Database
from keyboards import PREDEFINED_PROMPTS, build_prompt_picker, build_prompts_list_keyboard
from services.ocr_service import OCRService
from services.openrouter_service import OpenRouterService
from states import AiNoteStates, CustomPromptStates, ManualNoteStates, PromptTemplateStates


router = Router()


HELP_TEXT = (
    "Доступные команды:\n"
    "/addnote — создать заметку вручную\n"
    "/aiconcept — получить конспект с помощью ИИ\n"
    "/listnotes — посмотреть список заметок\n"
    "/note <id> — показать заметку\n"
    "/deletenote <id> — удалить заметку\n"
    "/setprompt — задать шаблон промпта по умолчанию\n"
    "/promptadd — сохранить именованный промпт\n"
    "/prompts — список и удаление промптов"
)


def chunk_text(text: str, limit: int = 3500) -> list[str]:
    text = text.strip()
    if not text:
        return []

    parts: list[str] = []
    while text:
        if len(text) <= limit:
            parts.append(text)
            break

        chunk = text[:limit]
        split_index = max(chunk.rfind("\n\n"), chunk.rfind("\n"), chunk.rfind(" "))
        if split_index <= 0:
            split_index = limit
        parts.append(text[:split_index].strip())
        text = text[split_index:].lstrip()

    return parts


def format_notes(notes: Iterable[dict]) -> str:
    lines: list[str] = []
    for item in notes:
        created = item.get("created_at")
        try:
            created_dt = datetime.fromisoformat(created)
            created = created_dt.strftime("%d.%m %H:%M")
        except Exception:
            pass
        lines.append(f"#{item['id']} · {item['title']} ({item['source']}, {created})")
    return "\n".join(lines)


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(
        "Привет! Я помогу вести цифровой мозг: создавай заметки вручную, генерируй конспекты с ИИ и вытягивай текст из файлов."
    )
    await message.answer(HELP_TEXT)


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(HELP_TEXT)


@router.message(Command("addnote"))
async def cmd_add_note(message: Message, state: FSMContext) -> None:
    await state.set_state(ManualNoteStates.waiting_for_title)
    await message.answer("Введите заголовок новой заметки:")


@router.message(ManualNoteStates.waiting_for_title)
async def manual_note_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if not title:
        await message.answer("Заголовок не может быть пустым. Попробуйте снова:")
        return
    await state.update_data(title=title)
    await state.set_state(ManualNoteStates.waiting_for_content)
    await message.answer("Теперь отправьте содержание заметки:")


@router.message(ManualNoteStates.waiting_for_content)
async def manual_note_content(message: Message, state: FSMContext, db: Database) -> None:
    content = (message.text or "").strip()
    if not content:
        await message.answer("Содержание не может быть пустым. Попробуйте снова:")
        return

    data = await state.get_data()
    title = data["title"]
    note_id = await db.add_note(
        user_id=message.from_user.id,
        title=title,
        content=content,
        source="manual",
    )
    await state.clear()
    await message.answer(f"Заметка #{note_id} сохранена.")


@router.message(Command("listnotes"))
async def cmd_list_notes(message: Message, db: Database) -> None:
    notes = await db.list_notes(message.from_user.id)
    if not notes:
        await message.answer("Пока нет заметок. Создайте первую с помощью /addnote или /aiconcept.")
        return
    await message.answer(format_notes(notes))


@router.message(Command("note"))
async def cmd_view_note(message: Message, command: CommandObject, db: Database) -> None:
    if not command.args:
        await message.answer("Используйте /note <id>.")
        return
    try:
        note_id = int(command.args.strip())
    except ValueError:
        await message.answer("ID заметки должен быть числом.")
        return

    note = await db.get_note(note_id, message.from_user.id)
    if not note:
        await message.answer("Заметка не найдена.")
        return

    text = f"#{note['id']} · {note['title']} ({note['source']})\n\n{note['content']}"
    for chunk in chunk_text(text):
        await message.answer(chunk)


@router.message(Command("deletenote"))
async def cmd_delete_note(message: Message, command: CommandObject, db: Database) -> None:
    if not command.args:
        await message.answer("Используйте /deletenote <id>.")
        return
    try:
        note_id = int(command.args.strip())
    except ValueError:
        await message.answer("ID заметки должен быть числом.")
        return

    deleted = await db.delete_note(note_id, message.from_user.id)
    if deleted:
        await message.answer("Заметка удалена.")
    else:
        await message.answer("Заметка не найдена.")


@router.message(Command("setprompt"))
async def cmd_set_prompt(message: Message, state: FSMContext) -> None:
    await state.set_state(PromptTemplateStates.waiting_for_template)
    await message.answer("Отправьте текст промпта. Вставьте {topic} туда, где нужно подставить тему.")


@router.message(PromptTemplateStates.waiting_for_template)
async def prompt_template_received(message: Message, state: FSMContext, db: Database) -> None:
    template = (message.text or "").strip()
    if "{topic}" not in template:
        await message.answer("В шаблоне должен присутствовать плейсхолдер {topic}. Попробуйте снова:")
        return

    await db.set_prompt_template(message.from_user.id, template)
    await state.clear()
    await message.answer("Шаблон сохранён. Теперь он будет использоваться по умолчанию.")


@router.message(Command("promptadd"))
async def cmd_prompt_add(message: Message, state: FSMContext) -> None:
    await state.set_state(CustomPromptStates.waiting_for_name)
    await message.answer("Введите название промпта:")


@router.message(CustomPromptStates.waiting_for_name)
async def prompt_add_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Название не может быть пустым. Попробуйте снова:")
        return

    await state.update_data(custom_prompt_name=name)
    await state.set_state(CustomPromptStates.waiting_for_template)
    await message.answer("Теперь отправьте текст промпта с плейсхолдером {topic}:")


@router.message(CustomPromptStates.waiting_for_template)
async def prompt_add_template(message: Message, state: FSMContext, db: Database) -> None:
    template = (message.text or "").strip()
    if "{topic}" not in template:
        await message.answer("В шаблоне должен присутствовать плейсхолдер {topic}. Попробуйте снова:")
        return

    data = await state.get_data()
    name = data["custom_prompt_name"]
    await db.upsert_custom_prompt(message.from_user.id, name, template)
    await state.clear()
    await message.answer(f"Промпт «{name}» сохранён.")


@router.message(Command("prompts"))
async def cmd_list_prompts(message: Message, db: Database) -> None:
    prompts = await db.list_custom_prompts(message.from_user.id)
    if not prompts:
        await message.answer("Пока нет сохранённых промптов. Добавьте новый командой /promptadd.")
        return

    keyboard = build_prompts_list_keyboard([(item["id"], item["name"]) for item in prompts])
    text = "Сохранённые промпты:\n" + "\n".join(f"• {item['name']}" for item in prompts)
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery) -> None:
    await callback.answer("Здесь нечего делать.", show_alert=False)


@router.callback_query(F.data.startswith("prompt:delete:"))
async def delete_prompt_callback(callback: CallbackQuery, db: Database) -> None:
    try:
        prompt_id = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer("Не удалось определить промпт.")
        return

    success = await db.delete_custom_prompt(callback.from_user.id, prompt_id)
    if not success:
        await callback.answer("Промпт не найден.")
        return

    prompts = await db.list_custom_prompts(callback.from_user.id)
    keyboard = build_prompts_list_keyboard([(item["id"], item["name"]) for item in prompts])
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer("Удалено.")


@router.message(Command("aiconcept"))
async def cmd_ai_concept(message: Message, state: FSMContext, openrouter_service: OpenRouterService) -> None:
    if not openrouter_service.is_configured():
        await message.answer("OpenRouter API ключ не настроен. Установите переменную OPENROUTER_API_KEY.")
        return

    await state.set_state(AiNoteStates.waiting_for_topic)
    await message.answer("Введите тему, по которой нужен конспект:")


@router.message(AiNoteStates.waiting_for_topic)
async def ai_topic_received(message: Message, state: FSMContext, db: Database) -> None:
    topic = (message.text or "").strip()
    if not topic:
        await message.answer("Тема не может быть пустой. Попробуйте снова:")
        return

    await state.update_data(topic=topic)
    prompts = await db.list_custom_prompts(message.from_user.id)
    keyboard = build_prompt_picker([(item["id"], item["name"]) for item in prompts])
    await state.set_state(AiNoteStates.waiting_for_prompt_name)
    await message.answer("Выберите промпт или пропустите:", reply_markup=keyboard)


@router.callback_query(AiNoteStates.waiting_for_prompt_name, F.data.startswith("prompt:"))
async def ai_prompt_selected(
    callback: CallbackQuery,
    state: FSMContext,
    db: Database,
    openrouter_service: OpenRouterService,
) -> None:
    data = await state.get_data()
    topic = data.get("topic")
    if not topic:
        await callback.answer("Не найдена тема. Начните заново командой /aiconcept.", show_alert=True)
        await state.clear()
        return

    template: str | None = None
    if callback.data == "prompt:skip":
        template = await db.get_prompt_template(callback.from_user.id)
    else:
        try:
            _, kind, value = callback.data.split(":", 2)
        except ValueError:
            await callback.answer("Не удалось распознать промпт.")
            return

        if kind == "pre":
            index = int(value)
            try:
                template = PREDEFINED_PROMPTS[index][1]
            except IndexError:
                await callback.answer("Промпт не найден.")
                return
        elif kind == "custom":
            prompt_id = int(value)
            prompt = await db.get_custom_prompt(callback.from_user.id, prompt_id)
            if not prompt:
                await callback.answer("Промпт не найден.")
                return
            template = prompt["template"]
        else:
            await callback.answer("Неизвестный тип промпта.")
            return

    await callback.answer("Готовлю конспект…")
    await callback.message.edit_reply_markup(reply_markup=None)

    try:
        note_text = await openrouter_service.generate_note(topic, template)
    except Exception as exc:
        await callback.message.answer(f"Не удалось получить ответ от модели: {exc}")
        await state.clear()
        return

    db_id = await db.add_note(
        user_id=callback.from_user.id,
        title=topic,
        content=note_text,
        source="ai",
    )

    header = f"Заметка #{db_id} создана.\n\n"
    chunks = chunk_text(note_text)
    if not chunks:
        await callback.message.answer(header + "Модель вернула пустой ответ.")
    else:
        first, *rest = chunks
        await callback.message.answer(header + first)
        for chunk in rest:
            await callback.message.answer(chunk)

    await state.clear()


async def _download_file(bot: Bot, file_id: str) -> bytes:
    buffer = io.BytesIO()
    await bot.download(file_id, destination=buffer)
    return buffer.getvalue()


@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot, db: Database, ocr_service: OCRService) -> None:
    photo = message.photo[-1]
    file_bytes = await _download_file(bot, photo.file_id)
    text = await ocr_service.extract_from_image(file_bytes)
    if not text:
        await message.answer("Не удалось распознать текст на изображении.")
        return

    title = message.caption or f"Изображение {photo.file_unique_id}"
    note_id = await db.add_note(
        user_id=message.from_user.id,
        title=title,
        content=text,
        source="ocr:image",
    )
    await message.answer(f"Текст распознан и сохранён в заметке #{note_id}.")
    for chunk in chunk_text(text):
        await message.answer(chunk)


@router.message(F.document.mime_type == "application/pdf")
async def handle_pdf(message: Message, bot: Bot, db: Database, ocr_service: OCRService) -> None:
    document = message.document
    file_bytes = await _download_file(bot, document.file_id)
    text = await ocr_service.extract_from_pdf(file_bytes)
    if not text:
        await message.answer("Не удалось извлечь текст из PDF.")
        return

    title = document.file_name or f"PDF {document.file_unique_id}"
    note_id = await db.add_note(
        user_id=message.from_user.id,
        title=title,
        content=text,
        source="ocr:pdf",
    )
    await message.answer(f"Текст из PDF сохранён в заметке #{note_id}.")
    for chunk in chunk_text(text):
        await message.answer(chunk)


@router.message(F.document.mime_type.in_({"image/jpeg", "image/png", "image/webp"}))
async def handle_document_image(message: Message, bot: Bot, db: Database, ocr_service: OCRService) -> None:
    document = message.document
    file_bytes = await _download_file(bot, document.file_id)
    text = await ocr_service.extract_from_image(file_bytes)
    if not text:
        await message.answer("Не удалось распознать текст в файле.")
        return

    title = document.file_name or f"Изображение {document.file_unique_id}"
    note_id = await db.add_note(
        user_id=message.from_user.id,
        title=title,
        content=text,
        source="ocr:image",
    )
    await message.answer(f"Текст из файла сохранён в заметке #{note_id}.")
    for chunk in chunk_text(text):
        await message.answer(chunk)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    settings = get_settings()
    db = Database(settings.database_path)
    await db.connect()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(router)

    openrouter_service = OpenRouterService(
        settings.openrouter_api_key,
        model=settings.openrouter_model,
        site_url=settings.openrouter_site_url,
    )
    if openrouter_service.is_configured():
        await openrouter_service.start()
    ocr_service = OCRService(settings.ocr_language)

    try:
        await dp.start_polling(
            bot,
            db=db,
            openrouter_service=openrouter_service,
            ocr_service=ocr_service,
            allowed_updates=dp.resolve_used_update_types(),
        )
    finally:
        await openrouter_service.aclose()
        await db.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
