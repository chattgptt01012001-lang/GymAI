# ==========================================
#               ИМПОРТЫ
# ==========================================

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.main_menu import main_menu_keyboard
from storage import get_user_profile, get_user_kbju
from keyboards.main_menu import (
    main_menu_keyboard,
    get_main_menu_text
)

from datetime import date

from storage import (
    get_premium_status,
    get_user_kbju,
    get_food_diary,
    get_water_amount,
)

# ==========================================
#            СОЗДАНИЕ ROUTER
# ==========================================

router = Router()


# ==========================================
#        БЕЗОПАСНОЕ УДАЛЕНИЕ СООБЩЕНИЯ
# ==========================================

async def delete_current_message(callback: CallbackQuery):

    try:

        await callback.message.delete()

    except Exception:

        pass

def food_menu_keyboard(is_premium=False):

    if is_premium:

        menu_button = InlineKeyboardButton(
            text="📋 Меню на день",
            callback_data="food_daily_menu"
        )

        diary_button = InlineKeyboardButton(
            text="📔 Дневник питания",
            callback_data="food_diary"
        )

        ai_button = InlineKeyboardButton(
            text="🤖 AI анализ питания",
            callback_data="food_ai_analysis"
        )

    else:

        menu_button = InlineKeyboardButton(
            text="💎 Меню на день",
            callback_data="food_daily_menu"
        )

        diary_button = InlineKeyboardButton(
            text="💎 Дневник питания",
            callback_data="food_diary"
        )

        ai_button = InlineKeyboardButton(
            text="💎 AI анализ питания",
            callback_data="food_ai_analysis"
        )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔥 Рассчитать КБЖУ",
                    callback_data="food_calculate_kbju"
                )
            ],
            [
                menu_button
            ],
            [
                diary_button
            ],
            [
                ai_button
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="back_to_main_menu"
                )
            ],
        ]
    )




# ==========================================
#              ПИТАНИЕ
# ==========================================

@router.callback_query(F.data == "menu_food")
async def open_food(callback: CallbackQuery):

    await delete_current_message(callback)

    is_premium = get_premium_status(callback.from_user.id)
    kbju = get_user_kbju(callback.from_user.id)

    today = str(date.today())
    food_diary = get_food_diary(callback.from_user.id)

    today_food = [
        meal for meal in food_diary
        if meal.get("date") == today
    ]

    total_calories = sum(meal.get("calories", 0) for meal in today_food)
    total_protein = sum(meal.get("protein", 0) for meal in today_food)
    total_fat = sum(meal.get("fat", 0) for meal in today_food)
    total_carbs = sum(meal.get("carbs", 0) for meal in today_food)

    water_ml = get_water_amount(
        callback.from_user.id,
        today
    )

    if not kbju:
        kbju_text = (
            "🔥 КБЖУ пока не рассчитано.\n\n"
            "Нажми кнопку ниже, чтобы рассчитать свою норму."
        )
    else:
        if is_premium:
            kbju_text = (
                "📊 <b>Сегодняшний прогресс</b>\n\n"
                f"🔥 Калории: <b>{total_calories} / {kbju['calories']} ккал</b>\n"
                f"🥩 Белки: <b>{total_protein} / {kbju['protein']} г</b>\n"
                f"🥑 Жиры: <b>{total_fat} / {kbju['fat']} г</b>\n"
                f"🍚 Углеводы: <b>{total_carbs} / {kbju['carbs']} г</b>\n\n"
                f"💧 Вода: <b>{water_ml} мл</b>"
            )
        else:
            kbju_text = (
                "🔥 <b>Твои нормы КБЖУ</b>\n\n"
                f"🔥 Калории: <b>{kbju['calories']} ккал</b>\n"
                f"🥩 Белки: <b>{kbju['protein']} г</b>\n"
                f"🥑 Жиры: <b>{kbju['fat']} г</b>\n"
                f"🍚 Углеводы: <b>{kbju['carbs']} г</b>"
            )

    if is_premium:
        premium_text = (
            "🤖 <b>Gym AI</b>\n\n"
            "Используй дневник, меню на день и AI-анализ, "
            "чтобы держать питание под контролем."
        )
    else:
        premium_text = (
            "💎 <b>Premium откроет:</b>\n\n"
            "• меню питания на день\n"
            "• дневник питания\n"
            "• учет воды\n"
            "• AI анализ рациона"
        )

    await callback.message.answer(
        "🍽 <b>ПИТАНИЕ</b>\n\n"
        "Твой центр контроля питания и калорий.\n\n"

        "━━━━━━━━━━━━━━\n\n"

        f"{kbju_text}\n\n"

        "━━━━━━━━━━━━━━\n\n"

        f"{premium_text}\n\n"

        "👇 <b>Выбери действие:</b>",
        reply_markup=food_menu_keyboard(is_premium),
        parse_mode="HTML"
    )

    await callback.answer()


# ==========================================
#            ТРЕНИРОВКИ
# ==========================================

@router.callback_query(F.data == "menu_workouts")
async def open_workouts(callback: CallbackQuery):

    # УДАЛЯЕМ ПРЕДЫДУЩЕЕ МЕНЮ
    await delete_current_message(callback)

    await callback.message.answer(
        "🏋️ <b>Тренировки</b>\n\n"
        "Этот раздел находится в разработке.\n\n"
        "Скоро здесь появятся:\n"
        "• планы тренировок\n"
        "• упражнения\n"
        "• программы под цель\n"
        "• AI тренер",

        parse_mode="HTML"
    )

    await callback.answer()


# ==========================================
#               ДНЕВНИК
# ==========================================

@router.callback_query(F.data == "menu_diary")
async def open_diary(callback: CallbackQuery):

    # УДАЛЯЕМ ПРЕДЫДУЩЕЕ МЕНЮ
    await delete_current_message(callback)

    await callback.message.answer(
        "📔 <b>Дневник</b>\n\n"
        "Здесь будет храниться:\n"
        "• история питания\n"
        "• тренировки\n"
        "• изменения веса\n"
        "• отслеживание прогресса",

        parse_mode="HTML"
    )

    await callback.answer()


# ==========================================
#             ПОДПИСКА
# ==========================================

@router.callback_query(F.data == "menu_subscription")
async def open_subscription(callback: CallbackQuery):

    # УДАЛЯЕМ ПРЕДЫДУЩЕЕ МЕНЮ
    await delete_current_message(callback)

    await callback.message.answer(
        "⭐ <b>Подписка Gym AI</b>\n\n"
        "В будущем здесь появятся:\n"
        "• PRO функции\n"
        "• AI рекомендации\n"
        "• расширенные планы питания\n"
        "• персональные тренировки",

        parse_mode="HTML"
    )

    await callback.answer()



# ==========================================
#         ВОЗВРАТ В ГЛАВНОЕ МЕНЮ
# ==========================================

@router.callback_query(F.data == "back_to_main_menu")
async def back_to_main_menu(callback: CallbackQuery):

    # Удаляем текущее меню
    await delete_current_message(callback)

    # Открываем новое главное меню
    await callback.message.answer(
        get_main_menu_text(
            callback.from_user.id
        ),
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()