import asyncio
import re
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# --- НАСТРОЙКИ ---
API_TOKEN = '8547568325:AAFf4kf1kJhzWq4f8ZqSO5yCLbpsFyViBqU'
CHANNEL_ID = '@Baraholka_amd'

# Впиши сюда ID свой и второго админа через запятую
ADMIN_IDS = [6585904616, 5394084759] 

BAN_FILE = "banned_users.txt"

# Загрузка забаненных из файла при старте
def load_banned():
    if os.path.exists(BAN_FILE):
        with open(BAN_FILE, "r") as f:
            return set(int(line.strip()) for line in f if line.strip().isdigit())
    return set()

# Сохранение забаненных в файл
def save_banned(user_id, action="add"):
    if action == "add":
        BANNED_USERS.add(user_id)
    else:
        BANNED_USERS.discard(user_id)
    
    with open(BAN_FILE, "w") as f:
        for uid in BANNED_USERS:
            f.write(f"{uid}\n")

BANNED_USERS = load_banned()
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class Form(StatesGroup):
    photo = State()
    description = State()
    price = State()
    link = State()

# --- ПРОВЕРКА НА БАН ---
@dp.message.outer_middleware()
async def ban_middleware(handler, event, data):
    if event.from_user.id in BANNED_USERS:
        return 
    return await handler(event, data)

# --- КОМАНДЫ АДМИНОВ ---
@dp.message(Command("ban"), F.from_user.id.in_(ADMIN_IDS))
async def cmd_ban(message: types.Message, command: CommandObject):
    if not command.args:
        return await message.answer("Пиши: /ban ID")
    try:
        uid = int(command.args)
        save_banned(uid, "add")
        await message.answer(f"🚫 Пользователь {uid} забанен обоими админами.")
    except:
        await message.answer("Нужно числовое ID.")

@dp.message(Command("unban"), F.from_user.id.in_(ADMIN_IDS))
async def cmd_unban(message: types.Message, command: CommandObject):
    try:
        uid = int(command.args)
        save_banned(uid, "remove")
        await message.answer(f"✅ Пользователь {uid} разбанен.")
    except:
        await message.answer("Ошибка в ID.")

# --- ОСНОВНАЯ ЛОГИКА ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer("Пришлите фото товара.")
    await state.set_state(Form.photo)

@dp.message(Form.photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await message.answer("Введите описание (без ссылок).")
    await state.set_state(Form.description)

@dp.message(Form.description)
async def process_description(message: types.Message, state: FSMContext):
    if re.search(r'http[s]?://|t\.me', message.text):
        return await message.answer("❌ Ссылки запрещены!")
    await state.update_data(description=message.text)
    await message.answer("Цена (только цифры):")
    await state.set_state(Form.price)

@dp.message(Form.price)
async def process_price(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Только цифры!")
    await state.update_data(price=message.text)
    await message.answer("Ссылка на Avito или Юлу:")
    await state.set_state(Form.link)

@dp.message(Form.link)
async def process_link(message: types.Message, state: FSMContext):
    url = message.text.lower()
    if "avito.ru" not in url and "youla.ru" not in url:
        return await message.answer("❌ Только Avito или Юла!")

    data = await state.get_data()
    author = f"@{message.from_user.username}" if message.from_user.username else "Скрыт"
    
    caption = (
        f"<b>📦 Товар:</b> {data['description']}\n"
        f"💰 <b>Цена:</b> {data['price']} руб.\n"
        f"🔗 <a href='{message.text}'>Ссылка</a>\n\n"
        f"👤 <b>Продавец:</b> {author}\n"
        f"🆔 <b>ID:</b> <code>{message.from_user.id}</code>"
    )

    await bot.send_photo(CHANNEL_ID, data['photo'], caption=caption, parse_mode="HTML")
    await message.answer("✅ Опубликовано!")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
