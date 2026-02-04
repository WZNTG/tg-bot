import asyncio
import re
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# --- НАСТРОЙКИ (ДАННЫЕ ОБНОВЛЕНЫ) ---
API_TOKEN = '8547568325:AAFf4kf1kJhzWq4f8ZqSO5yCLbpsFyViBqU'
CHANNEL_ID = 'baraholka_amd'

# ID двух админов (твои данные)
ADMIN_IDS = [6585904616, 5394084759] 

BAN_FILE = "banned_users.txt"

# --- ЛОГИКА БАНА ---
def load_banned():
    if os.path.exists(BAN_FILE):
        with open(BAN_FILE, "r") as f:
            return set(int(line.strip()) for line in f if line.strip().isdigit())
    return set()

def save_banned_to_file():
    with open(BAN_FILE, "w") as f:
        for uid in BANNED_USERS:
            f.write(f"{uid}\n")

BANNED_USERS = load_banned()

# --- ИНИЦИАЛИЗАЦИЯ ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class Form(StatesGroup):
    photo = State()
    description = State()
    price = State()
    link = State()

# Middleware для проверки бана (если чел в списке, бот молчит)
@dp.message.outer_middleware()
async def ban_middleware(handler, event, data):
    if event.from_user and event.from_user.id in BANNED_USERS:
        return 
    return await handler(event, data)

# --- КОМАНДЫ АДМИНОВ ---
@dp.message(Command("ban"), F.from_user.id.in_(ADMIN_IDS))
async def cmd_ban(message: types.Message, command: CommandObject):
    if not command.args:
        return await message.answer("Пример: /ban 12345678")
    try:
        uid = int(command.args)
        BANNED_USERS.add(uid)
        save_banned_to_file()
        await message.answer(f"🚫 Пользователь {uid} забанен навсегда.")
    except:
        await message.answer("Ошибка: ID должен быть числом.")

@dp.message(Command("unban"), F.from_user.id.in_(ADMIN_IDS))
async def cmd_unban(message: types.Message, command: CommandObject):
    if not command.args:
        return await message.answer("Пример: /unban 12345678")
    try:
        uid = int(command.args)
        if uid in BANNED_USERS:
            BANNED_USERS.remove(uid)
            save_banned_to_file()
            await message.answer(f"✅ Пользователь {uid} разбанен.")
        else:
            await message.answer("Этот ID не был в бане.")
    except:
        await message.answer("Ошибка в ID.")

# --- ОСНОВНОЙ ПРОЦЕСС ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Привет! Начнем создание объявления.\nПришлите 1 фото товара.")
    await state.set_state(Form.photo)

@dp.message(Form.photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await message.answer("Отлично! Теперь введите описание (без любых ссылок).")
    await state.set_state(Form.description)

@dp.message(Form.description)
async def process_description(message: types.Message, state: FSMContext):
    # Запрет любых ссылок в тексте описания
    if re.search(r'http[s]?://|t\.me', message.text):
        return await message.answer("❌ Ссылки в описании запрещены! Напишите текст без ссылок.")
    await state.update_data(description=message.text)
    await message.answer("Введите цену (только цифры):")
    await state.set_state(Form.price)

@dp.message(Form.price)
async def process_price(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("❌ Ошибка! Введите только число (например, 1500).")
    await state.update_data(price=message.text)
    await message.answer("Вставьте ссылку на Avito или Юлу (обязательно):")
    await state.set_state(Form.link)

@dp.message(Form.link)
async def process_link(message: types.Message, state: FSMContext):
    user_url = message.text.lower()
    # Проверка на обязательное наличие Avito или Юлы
    if "avito.ru" not in user_url and "youla.ru" not in user_url:
        return await message.answer("❌ Ошибка! Допускаются только ссылки на Avito или Юлу.")

    data = await state.get_data()
    author = f"@{message.from_user.username}" if message.from_user.username else "Скрыт"
    
    caption = (
        f"<b>📦 Новое объявление</b>\n\n"
        f"📝 {data['description']}\n\n"
        f"💰 <b>Цена:</b> {data['price']} руб.\n"
        f"🔗 <a href='{message.text}'>Посмотреть на площадке</a>\n\n"
        f"👤 <b>Продавец:</b> {author}\n"
        f"🆔 <b>ID:</b> <code>{message.from_user.id}</code>\n\n"
        f"🤖 <b>Выложить свой товар в барахолку — @amdBaraxolkabot</b>"
    )

    try:
        await bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=data['photo'],
            caption=caption,
            parse_mode="HTML"
        )
        await message.answer("✅ Чотко! Объявление опубликовано в канале.")
    except Exception as e:
        await message.answer(f"❌ Ошибка отправки: {e}")
    
    await state.clear()

async def main():
    print("Бот запущен на вашем ПК...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен.")