# ==========================================
#               ИМПОРТЫ
# ==========================================

from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from storage import (
    get_user_profile,
    get_workout_history,
    get_premium_status,
)

# ==========================================
#            ГЛАВНОЕ МЕНЮ
# ==========================================

def get_main_menu_text(user_id):

    profile = get_user_profile(user_id)
    workout_history = get_workout_history(user_id)
    is_premium = get_premium_status(user_id)

    premium_text = (
        "🟢 Premium"
        if is_premium
        else "⚪ Free"
    )

    if profile:
        weight = profile.get("weight", "--")
        goal = profile.get("goal", "--")
    else:
        weight = "--"
        goal = "--"

    goal_map = {
        "loss": "Похудение",
        "gain": "Набор массы",
        "maintain": "Поддержание формы",
    }

    goal_text = goal_map.get(goal, goal)

    total_workouts = len(workout_history)

    if workout_history:
        last_workout = workout_history[-1].get("date", "неизвестно")
    else:
        last_workout = "нет данных"

    return (
        "<b>GYM AI</b>\n"
        "Твой AI ассистент для тренировок и питания.\n\n"

        "📊 <b>Твой статус:</b>\n"
        f"⚖️ Вес: <b>{weight} кг</b>\n"
        f"🎯 Цель: <b>{goal_text}</b>\n"
        f"🏋️ Тренировок всего: <b>{total_workouts}</b>\n"
        f"🔥 Последняя тренировка: <b>{last_workout}</b>\n"
        f"💎 Тариф: <b>{premium_text}</b>\n\n"

        "<b>Gym AI помогает:</b>\n"
        "• строить тело\n"
        "• анализировать прогресс\n"
        "• контролировать питание\n"
        "• улучшать форму\n\n"

    )


def main_menu_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="👤 Профиль",
                    callback_data="menu_profile"
                ),

                InlineKeyboardButton(
                    text="🤖 AI Коуч",
                    callback_data="ai_coach"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🏋️ Тренировки",
                    callback_data="menu_workout"
                ),

                InlineKeyboardButton(
                    text="🍽 Питание",
                    callback_data="menu_food"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💎 Premium",
                    callback_data="subscription"
                )
            ],
        ]
    )