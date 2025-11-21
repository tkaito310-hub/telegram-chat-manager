# file: manager_bot.py
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import Command, ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER
from aiogram.enums import ChatMemberStatus
import asyncio
import re
import time

API_TOKEN = "8532258849:AAGayzlJ_jF5GPICfR7KWVpUKPdDJMRnjdU"  # ← ВСТАВЬ СЮДА СВОЙ ТОКЕН

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

# Антимат (добавляй свои слова)
BAD_WORDS = ["мамашу"]

# Антифлуд (сообщения → мут на 10 минут)
flood_control = {}

# Приветствие новых участников + кнопка "Я не бот"
@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> IS_MEMBER))
async def welcome(update: ChatMemberUpdated):
    user = update.new_chat_member.user
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Я не робот ✅", callback_data="im_not_bot")]
    ])
    await update.answer(
        f"Привет, {user.mention_html()}!\n"
        "Нажми кнопку ниже, чтобы пройти проверку 👇",
        reply_markup=keyboard
    )

# Обработка нажатия кнопки
@router.callback_query(F.data == "im_not_bot")
async def not_bot(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(f"{callback.from_user.mention_html()} прошёл проверку ✅")

# Основная обработка сообщений
@router.message(F.chat.type.in_({"supergroup", "group"}))
async def message_handler(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # === Антифлуд ===
    now = time.time()
    if user_id not in flood_control:
        flood_control[user_id] = []
    flood_control[user_id] = [t for t in flood_control[user_id] if now - t < 3]
    flood_control[user_id].append(now)

    if len(flood_control[user_id]) > 5:  # 5 сообщений за 3 секунды
        until = int(now + 1200)  # мут на 20 минут
        await message.chat.restrict_member(user_id, can_send_messages=False, until_date=until)
        await message.answer(f"{message.from_user.mention_html()} замучен на 10 мин за флуд ⏱️")
        return

    # === Антимат ===
    if message.text:
        text = message.text.lower()
        if any(bad in text for bad in BAD_WORDS):
            await message.delete()
            await message.answer(f"{message.from_user.mention_html()}, мат запрещён ⚠️")
            return

    # === Удаление служе نیزных сообщений (кто вошёл/вышел) ===
    if message.new_chat_members or message.left_chat_member:
        await message.delete()

# Команда /ban @user
@router.message(Command("ban"))
async def ban_user(message: Message):
    if message.reply_to_message:
        admin = await message.chat.get_member(message.from_user.id)
        if admin.status not in ["administrator", "creator"]:
            return
        target = message.reply_to_message.from_user
        await message.chat.ban_sender_chat(target.id)
        await message.answer(f"{target.mention_html()} забанен навсегда")

dp.include_router(router)

async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
