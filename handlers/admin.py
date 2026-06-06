# ==========================================
#               ИМПОРТЫ
# ==========================================

from aiogram import Router
from aiogram.types import Message

from config import ADMIN_IDS

from storage import (
    get_premium_status,
    set_premium_status,
)

import json
import os


# ==========================================
#               ROUTER
# ==========================================

router = Router()


# ==========================================
#      ЗАГРУЗКА ВСЕХ ПОЛЬЗОВАТЕЛЕЙ
# ==========================================

USERS_FILE = "users.json"


def load_all_users():

    if not os.path.exists(USERS_FILE):
        return {}

    with open(USERS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

# ==========================================
#          ПРОВЕРКА АДМИНА
# ==========================================

def is_admin(user_id):

    return user_id in ADMIN_IDS


# ==========================================
#              ADMIN HELP
# ==========================================

@router.message(lambda message: message.text == "/admin")
async def admin_panel(message: Message):

    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "🛠 <b>Админка Gym AI</b>\n\n"

        "Команды:\n\n"

        "💎 Выдать Premium\n"
        "<code>/premium_on user_id</code>\n\n"

        "🆓 Снять Premium\n"
        "<code>/premium_off user_id</code>\n\n"

        "📊 Проверить статус\n"
        "<code>/premium_status user_id</code>\n\n"

        "👥 Список пользователей\n"
        "<code>/users</code>\n\n"

        "👤 Карточка пользователя\n"
        "<code>/user user_id</code>\n\n"

        "Пример:\n"
        "<code>/premium_on 123456789</code>",

        parse_mode="HTML"
    )


# ==========================================
#              ВЫДАТЬ PREMIUM
# ==========================================

@router.message(lambda message: message.text.startswith("/premium_on"))
async def premium_on_handler(message: Message):

    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()

    if len(parts) != 2:

        await message.answer(
            "❌ Используй:\n"
            "<code>/premium_on user_id</code>",
            parse_mode="HTML"
        )

        return

    user_id = parts[1]

    set_premium_status(
        user_id,
        True
    )

    await message.answer(
        "✅ <b>Premium выдан</b>\n\n"
        f"ID: <code>{user_id}</code>",
        parse_mode="HTML"
    )


# ==========================================
#              СНЯТЬ PREMIUM
# ==========================================

@router.message(lambda message: message.text.startswith("/premium_off"))
async def premium_off_handler(message: Message):

    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()

    if len(parts) != 2:

        await message.answer(
            "❌ Используй:\n"
            "<code>/premium_off user_id</code>",
            parse_mode="HTML"
        )

        return

    user_id = parts[1]

    set_premium_status(
        user_id,
        False
    )

    await message.answer(
        "🆓 <b>Premium отключен</b>\n\n"
        f"ID: <code>{user_id}</code>",
        parse_mode="HTML"
    )


# ==========================================
#              СТАТУС PREMIUM
# ==========================================

@router.message(lambda message: message.text.startswith("/premium_status"))
async def premium_status_handler(message: Message):

    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()

    if len(parts) != 2:

        await message.answer(
            "❌ Используй:\n"
            "<code>/premium_status user_id</code>",
            parse_mode="HTML"
        )

        return

    user_id = parts[1]

    is_premium = get_premium_status(
        user_id
    )

    status_text = (
        "💎 Premium"
        if is_premium
        else "🆓 Free"
    )

    await message.answer(
        "📊 <b>Статус пользователя</b>\n\n"
        f"ID: <code>{user_id}</code>\n"
        f"Статус: <b>{status_text}</b>",
        parse_mode="HTML"
    )


# ==========================================
#              СПИСОК ПОЛЬЗОВАТЕЛЕЙ
# ==========================================

@router.message(lambda message: message.text == "/users")
async def users_handler(message: Message):

    if not is_admin(message.from_user.id):
        return

    users = load_all_users()

    total_users = len(users)

    premium_count = 0
    free_count = 0

    for user_id, user_data in users.items():

        if user_data.get("premium") is True:
            premium_count += 1
        else:
            free_count += 1

    await message.answer(
        "👥 <b>Пользователи Gym AI</b>\n\n"
        f"Всего пользователей: <b>{total_users}</b>\n\n"
        f"💎 Premium: <b>{premium_count}</b>\n"
        f"🆓 Free: <b>{free_count}</b>\n\n"
        "Чтобы посмотреть пользователя:\n"
        "<code>/user user_id</code>",
        parse_mode="HTML"
    )


# ==========================================
#              ДАННЫЕ ПОЛЬЗОВАТЕЛЯ
# ==========================================

@router.message(lambda message: message.text.startswith("/user"))
async def user_info_handler(message: Message):

    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()

    if len(parts) != 2:
        await message.answer(
            "❌ Используй:\n"
            "<code>/user user_id</code>",
            parse_mode="HTML"
        )
        return

    user_id = parts[1]

    users = load_all_users()

    user_data = users.get(str(user_id))

    if not user_data:
        await message.answer(
            "❌ Пользователь не найден.",
            parse_mode="HTML"
        )
        return

    premium_status = (
        "💎 Premium"
        if user_data.get("premium") is True
        else "🆓 Free"
    )

    profile = user_data.get("profile", {})
    kbju = user_data.get("kbju", {})
    workout_history = user_data.get("workout_history", [])
    food_diary = user_data.get("food_diary", [])

    await message.answer(
        "👤 <b>Карточка пользователя</b>\n\n"
        f"ID: <code>{user_id}</code>\n"
        f"Статус: <b>{premium_status}</b>\n\n"

        "📌 <b>Профиль</b>\n"
        f"Пол: <b>{profile.get('gender', '—')}</b>\n"
        f"Возраст: <b>{profile.get('age', '—')}</b>\n"
        f"Рост: <b>{profile.get('height', '—')}</b>\n"
        f"Вес: <b>{profile.get('weight', '—')}</b>\n"
        f"Цель: <b>{profile.get('goal', '—')}</b>\n\n"

        "🔥 <b>КБЖУ</b>\n"
        f"Калории: <b>{kbju.get('calories', '—')}</b>\n"
        f"Белки: <b>{kbju.get('protein', '—')}</b>\n"
        f"Жиры: <b>{kbju.get('fat', '—')}</b>\n"
        f"Углеводы: <b>{kbju.get('carbs', '—')}</b>\n\n"

        "🏋️ <b>Активность</b>\n"
        f"Тренировок: <b>{len(workout_history)}</b>\n"
        f"Записей питания: <b>{len(food_diary)}</b>",
        parse_mode="HTML"
    )