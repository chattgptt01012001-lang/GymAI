# ==========================================
#               ИМПОРТЫ
# ==========================================

from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import (
    State,
    StatesGroup,
)

from openai import OpenAI
from config import OPENAI_API_KEY
from storage import (
    save_workout_plan,
    get_workout_plan,
    delete_workout_plan,
    add_workout_history_entry,
    get_workout_history,
    delete_workout_history_entry,
    get_user_profile,
    get_premium_status,
)

from datetime import date, timedelta

# ==========================================
#               ROUTER
# ==========================================

router = Router()
client = OpenAI(
    api_key=OPENAI_API_KEY,
    timeout=60
)


# ==========================================
#          СОСТОЯНИЯ СОЗДАНИЯ ПЛАНА
# ==========================================

class CreateWorkoutPlan(StatesGroup):

    goal = State()
    location = State()
    confirm_location = State()
    level = State()
    workouts_per_week = State()
    working_weights = State()
    focus = State()
    limitations = State()

class LogWorkoutForm(StatesGroup):

    workout_text = State()


# ==========================================
#       КЛАВИАТУРА МЕСТ ТРЕНИРОВОК
# ==========================================

def workout_locations_keyboard(selected=None):

    if selected is None:
        selected = []

    locations = {

        "gym": "🏋️ Зал",

        "home": "🏠 Дом",

        "street": "🏃 Улица",

        "bar": "💪 Турник",

        "playground": "⚽ Спортплощадка",
    }

    buttons = []

    for key, text in locations.items():

        is_selected = key in selected

        prefix = "✅ " if is_selected else "☑️ "

        buttons.append([
            InlineKeyboardButton(
                text=prefix + text,
                callback_data=f"toggle_location_{key}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="➡️ Продолжить",
            callback_data="confirm_locations"
        )
    ])

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


# ==========================================
#        КЛАВИАТУРА ТРЕНИРОВОК
# ==========================================

def workout_menu_keyboard(is_premium=False):

    if is_premium:
        advanced_plan_text = "🧠 Продвинутый AI план"
        ai_analysis_text = "📊 AI анализ тренировок"
    else:
        advanced_plan_text = "💎 Продвинутый AI план"
        ai_analysis_text = "💎 AI анализ тренировок"

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="📋 Мой план",
                    callback_data="my_workout_plan"
                )
            ],

            [
                InlineKeyboardButton(
                    text="▶️ Начать тренировку",
                    callback_data="start_workout_from_plan"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📝 Записать тренировку",
                    callback_data="log_workout"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📊 История и прогресс",
                    callback_data="workout_stats"
                )
            ],

            [
                InlineKeyboardButton(
                    text=ai_analysis_text,
                    callback_data="ai_workout_analysis"
                )
            ],

            [
                InlineKeyboardButton(
                    text="➕ Создать план",
                    callback_data="create_workout_plan_free"
                )
            ],

            [
                InlineKeyboardButton(
                    text=advanced_plan_text,
                    callback_data="create_workout_plan"
                )
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
#        КЛАВИАТУРА ФОКУСА ТРЕНИРОВОК
# ==========================================

def workout_focus_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🍑 Ягодицы / ноги",
                    callback_data="focus_glutes_legs"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💪 Верх тела",
                    callback_data="focus_upper_body"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏋️ Сила",
                    callback_data="focus_strength"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔥 Жиросжигание",
                    callback_data="focus_fat_loss"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚖️ Баланс всего тела",
                    callback_data="focus_balance"
                )
            ],
        ]
    )


# ==========================================
#          ОТКРЫТЬ ТРЕНИРОВКИ
# ==========================================

@router.callback_query(F.data == "menu_workout")
async def workout_menu_handler(callback: CallbackQuery):

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
    "🏋️ <b>Тренировки Gym AI</b>\n\n"

    "Твой персональный центр тренировок.\n\n"

    "📋 Создавай планы под свою цель\n"
    "▶️ Выполняй тренировки по готовому плану\n"
    "📝 Записывай выполненные тренировки\n"
    "📊 Отслеживай прогресс\n"
    "🤖 Получай рекомендации Gym AI\n\n"

    "Каждая тренировка приближает тебя к результату.",

    reply_markup=workout_menu_keyboard(
        get_premium_status(callback.from_user.id)
    ),
    parse_mode="HTML"
    )

    await callback.answer()


# ==========================================
#         СОЗДАНИЕ PREMIUM ПЛАНА — ЦЕЛЬ
# ==========================================

@router.callback_query(F.data == "create_workout_plan")
async def create_workout_plan(callback: CallbackQuery, state: FSMContext):

    try:
        await callback.message.delete()
    except Exception:
        pass

    # ==========================================
    #          ПРОВЕРКА PREMIUM
    # ==========================================

    is_premium = get_premium_status(
        callback.from_user.id
    )

    if not is_premium:

        await callback.message.answer(
            "💎 <b>Продвинутый AI план доступен в Premium</b>\n\n"
            "Premium откроет:\n"
            "• учёт рабочих весов\n"
            "• фокус тренировок\n"
            "• ограничения и травмы\n"
            "• прогрессию нагрузки на 4 недели\n"
            "• более точный персональный план\n\n"
            "Чтобы открыть функцию — активируй Premium.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="💎 Открыть Premium",
                            callback_data="subscription"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🏋️ Назад",
                            callback_data="menu_workout"
                        )
                    ],
                ]
            ),
            parse_mode="HTML"
        )

        await callback.answer()
        return

    # ==========================================
    #          СОХРАНЯЕМ ТИП ПЛАНА
    # ==========================================

    await state.update_data(
        workout_plan_type="premium"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔥 Набор массы",
                    callback_data="goal_mass"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚖️ Похудение",
                    callback_data="goal_weight_loss"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏃 Поддержание формы",
                    callback_data="goal_maintenance"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏋️ Назад",
                    callback_data="menu_workout"
                )
            ],
        ]
    )

    await callback.message.answer(
        "💎 <b>Продвинутый AI план</b>\n\n"
        "Gym AI создаст персональную программу с учетом цели, "
        "уровня, рабочих весов, фокуса и ограничений.\n\n"
        "Выбери основную цель 👇",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await state.set_state(
        CreateWorkoutPlan.goal
    )

    await callback.answer()


# ==========================================
#         ОБРАБОТЧИК ВЫБОРА ЦЕЛИ
# ==========================================

@router.callback_query(F.data.startswith("goal_"))
async def workout_goal_handler(
    callback: CallbackQuery,
    state: FSMContext
):

    goal_map = {
        "goal_mass": "Набор массы",
        "goal_weight_loss": "Похудение",
        "goal_maintenance": "Поддержание формы",
    }

    goal = goal_map.get(callback.data)

    await state.update_data(
        goal=goal
    )

    try:
        await callback.message.delete()
    except Exception:
        pass

    data = await state.get_data()

    workout_plan_type = data.get(
        "workout_plan_type",
        "premium"
    )

    if workout_plan_type == "free":

        await callback.message.answer(
            "📍 <b>Где ты тренируешься?</b>\n\n"
            "Выбери место, где тебе удобно тренироваться.\n\n"
            "Для базового плана Gym AI подберёт простые упражнения под доступный инвентарь 👇",
            reply_markup=workout_locations_keyboard(),
            parse_mode="HTML"
        )

    else:

        await callback.message.answer(
            "📍 <b>Где ты тренируешься?</b>\n\n"
            "Выбери все места, где тебе удобно тренироваться.\n\n"
            "Gym AI подберёт упражнения под доступный инвентарь 👇",
            reply_markup=workout_locations_keyboard(),
            parse_mode="HTML"
        )

    await state.set_state(
        CreateWorkoutPlan.location
    )

    await callback.answer()

# ==========================================
#       ВЫБОР МЕСТ ТРЕНИРОВОК
# ==========================================

@router.callback_query(F.data.startswith("toggle_location_"))
async def toggle_location_handler(
    callback: CallbackQuery,
    state: FSMContext
):

    data = await state.get_data()

    selected = data.get("locations", [])

    location = callback.data.replace("toggle_location_", "")

    if location in selected:
        selected.remove(location)
    else:
        selected.append(location)

    await state.update_data(
        locations=selected
    )

    await callback.message.edit_reply_markup(
        reply_markup=workout_locations_keyboard(selected)
    )

    await callback.answer()


# ==========================================
#      ПОДТВЕРЖДЕНИЕ МЕСТ ТРЕНИРОВОК
# ==========================================

@router.callback_query(F.data == "confirm_locations")
async def confirm_locations_handler(
    callback: CallbackQuery,
    state: FSMContext
):

    data = await state.get_data()

    selected = data.get("locations", [])

    if not selected:

        await callback.answer(
            "Выбери хотя бы одно место",
            show_alert=True
        )

        return

    try:
        await callback.message.delete()
    except Exception:
        pass

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🟢 Новичок",
                    callback_data="level_beginner"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🟡 Средний",
                    callback_data="level_intermediate"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔴 Продвинутый",
                    callback_data="level_advanced"
                )
            ],
        ]
    )

    await callback.message.answer(
        "📈 <b>Уровень подготовки</b>\n\n"
        "Это поможет подобрать безопасную нагрузку и правильный объём.\n\n"
        "Выбери вариант, который ближе всего к тебе",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await state.set_state(
        CreateWorkoutPlan.level
    )

    await callback.answer()


# ==========================================
#              ВЫБОР УРОВНЯ
# ==========================================

@router.callback_query(F.data.startswith("level_"))
async def workout_level_handler(
    callback: CallbackQuery,
    state: FSMContext
):

    level_map = {
        "level_beginner": "Новичок",
        "level_intermediate": "Средний",
        "level_advanced": "Продвинутый",
    }

    level = level_map.get(callback.data)

    await state.update_data(
        level=level
    )

    try:
        await callback.message.delete()
    except Exception:
        pass

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="2 раза в неделю",
                    callback_data="workouts_2"
                )
            ],
            [
                InlineKeyboardButton(
                    text="3 раза в неделю",
                    callback_data="workouts_3"
                )
            ],
            [
                InlineKeyboardButton(
                    text="4 раза в неделю",
                    callback_data="workouts_4"
                )
            ],
            [
                InlineKeyboardButton(
                    text="5 раз в неделю",
                    callback_data="workouts_5"
                )
            ],
            [
                InlineKeyboardButton(
                    text="6 раз в неделю",
                    callback_data="workouts_6"
                )
            ],
        ]
    )

    await callback.message.answer(
        "📅 <b>Частота тренировок</b>\n\n"
        "Сколько раз в неделю ты реально готов тренироваться?\n\n"
        "Лучше выбрать стабильный график, чем перегрузить себя",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await state.set_state(
        CreateWorkoutPlan.workouts_per_week
    )

    await callback.answer()


# ==========================================
#        ВЫБОР КОЛИЧЕСТВА ТРЕНИРОВОК
# ==========================================

@router.callback_query(F.data.startswith("workouts_"))
async def workouts_per_week_handler(
    callback: CallbackQuery,
    state: FSMContext
):

    workouts_per_week = callback.data.replace(
        "workouts_",
        ""
    )

    await state.update_data(
        workouts_per_week=workouts_per_week
    )

    try:
        await callback.message.delete()
    except Exception:
        pass

    data = await state.get_data()

    workout_plan_type = data.get(
        "workout_plan_type",
        "premium"
    )

    # ==========================================
    #          FREE ПЛАН — СРАЗУ ГЕНЕРАЦИЯ
    # ==========================================

    if workout_plan_type == "free":

        profile = get_user_profile(
            callback.from_user.id
        )

        loading_message = await callback.message.answer(
            "🤖 <b>Gym AI создает базовый план...</b>\n\n"
            "Подбираю упражнения под цель, уровень и место тренировок.",
            parse_mode="HTML"
        )

        try:

            response = client.responses.create(
                model="gpt-4.1-mini",
                input=(
                    "Ты профессиональный фитнес-тренер Gym AI.\n"
                    "Создай базовый план тренировок на русском языке.\n\n"

                    "Это FREE-план, поэтому он должен быть проще, чем Premium.\n\n"

                    "ДАННЫЕ ПОЛЬЗОВАТЕЛЯ:\n"
                    f"Профиль пользователя: {profile}\n"
                    f"Цель: {data['goal']}\n"
                    f"Места тренировок: {', '.join(data['locations'])}\n"
                    f"Уровень: {data['level']}\n"
                    f"Тренировок в неделю: {data['workouts_per_week']}\n\n"

                    "ТРЕБОВАНИЯ:\n"
                    "- составь простой и безопасный план\n"
                    "- учитывай цель, уровень и место тренировок\n"
                    "- не используй сложную периодизацию\n"
                    "- не указывай точные рабочие веса\n"
                    "- дай подходы, повторения и отдых\n"
                    "- упражнения должны соответствовать месту тренировок\n"
                    "- план должен быть понятным новичку\n\n"

                    "ФОРМАТ ОТВЕТА:\n\n"
                    "🆓 <b>БАЗОВЫЙ ПЛАН ТРЕНИРОВОК</b>\n\n"

                    "Коротко опиши цель плана.\n\n"

                    "Раздели план по тренировочным дням.\n\n"

                    "Для каждого упражнения укажи:\n"
                    "- подходы\n"
                    "- повторения\n"
                    "- отдых между подходами\n\n"

                    "💎 <b>Что даст Premium</b>\n"
                    "• план с учетом рабочих весов\n"
                    "• индивидуальную прогрессию на 4 недели\n"
                    "• учет ограничений и травм\n"
                    "• акцент на нужные мышцы и цель\n"
                    "• более точную нагрузку под твой уровень\n"
                    "• AI анализ тренировок и прогресса\n\n"

                    "Не используй теги <br>, <ul>, <li>, <p>. Только <b>.\n"
                    "Не используй Markdown. Используй только HTML <b>."
                )
            )

            workout_plan = (
                response.output_text
                .replace("<br>", "\n")
                .replace("<br/>", "\n")
                .replace("<br />", "\n")
            )

        except Exception as e:

            print("FREE WORKOUT PLAN ERROR:", e)

            try:
                await loading_message.delete()
            except Exception:
                pass

            await callback.message.answer(
                "⚠️ Не удалось создать базовый план тренировок.\n\n"
                "Попробуй ещё раз через пару секунд.",
                reply_markup=workout_menu_keyboard(),
                parse_mode="HTML"
            )

            await state.clear()
            await callback.answer()
            return

        try:
            await loading_message.delete()
        except Exception:
            pass

        save_workout_plan(
            callback.from_user.id,
            {
                "type": "free",
                "goal": data["goal"],
                "locations": data["locations"],
                "level": data["level"],
                "workouts_per_week": data["workouts_per_week"],
                "working_weights": "не указано",
                "focus": "Базовый план",
                "limitations": "не указано",
                "plan_text": workout_plan,
            }
        )

        await callback.message.answer(
            workout_plan,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="▶️ Начать тренировку",
                            callback_data="start_workout_from_plan"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="💎 Продвинутый AI план",
                            callback_data="create_workout_plan"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🏠 Главное меню",
                            callback_data="back_to_main_menu"
                        )
                    ],
                ]
            ),
            parse_mode="HTML"
        )

        await state.clear()
        await callback.answer()
        return

    # ==========================================
    #          PREMIUM ПЛАН — ИДЕМ ДАЛЬШЕ
    # ==========================================

    weights_message = await callback.message.answer(
        "🏋️ <b>Рабочие веса</b>\n\n"
        "Напиши свои примерные рабочие веса — это поможет точнее подобрать нагрузку.\n\n"
        "<i>Например:\n"
        "Жим лежа 60×8\n"
        "Присед 80×8\n"
        "Тяга 100×5</i>\n\n"
        "Если не знаешь — напиши: <b>не знаю</b>",
        parse_mode="HTML"
    )

    await state.update_data(
        weights_message_id=weights_message.message_id
    )

    await state.set_state(
        CreateWorkoutPlan.working_weights
    )

    await callback.answer()


# ==========================================
#          ОБРАБОТКА РАБОЧИХ ВЕСОВ
# ==========================================

@router.message(CreateWorkoutPlan.working_weights)
async def workout_working_weights_handler(
    message: Message,
    state: FSMContext
):

    working_weights = message.text

    try:
        await message.delete()
    except Exception:
        pass


    data = await state.get_data()

    weights_message_id = data.get(
        "weights_message_id"
    )

    if weights_message_id:

        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=weights_message_id
            )
        except Exception:
            pass


    await state.update_data(
        working_weights=working_weights
    )


    focus_message = await message.answer(
        "🎯 <b>Фокус тренировок</b>\n\n"
        "Выбери главный акцент программы.\n\n"
        "Gym AI сохранит баланс, но усилит нужное направление",
        reply_markup=workout_focus_keyboard(),
        parse_mode="HTML"
    )

    await state.update_data(
        focus_message_id=focus_message.message_id
    )

    await state.set_state(
        CreateWorkoutPlan.focus
    )


# ==========================================
#          ОБРАБОТКА ФОКУСА ТРЕНИРОВОК
# ==========================================

@router.callback_query(F.data.startswith("focus_"))
async def workout_focus_handler(
    callback: CallbackQuery,
    state: FSMContext
):

    focus_map = {
        "focus_glutes_legs": "Ягодицы / ноги",
        "focus_upper_body": "Верх тела",
        "focus_strength": "Сила",
        "focus_fat_loss": "Жиросжигание",
        "focus_balance": "Баланс всего тела",
    }

    focus = focus_map.get(callback.data, "Баланс всего тела")

    await state.update_data(
        focus=focus
    )

    try:
        await callback.message.delete()
    except Exception:
        pass

    limitations_message = await callback.message.answer(
        "⚠️ <b>Есть ли ограничения, травмы или противопоказания?</b>\n\n"
        "Напиши кратко текстом.\n\n"
        "<i>Например: болит поясница, нельзя приседать, нет ограничений</i>",
        parse_mode="HTML"
    )

    await state.update_data(
        limitations_message_id=limitations_message.message_id
    )

    await state.set_state(
        CreateWorkoutPlan.limitations
    )

    await callback.answer()


# ==========================================
#      ОБРАБОТКА ОГРАНИЧЕНИЙ И ГЕНЕРАЦИЯ
# ==========================================

@router.message(CreateWorkoutPlan.limitations)
async def workout_limitations_handler(
    message: Message,
    state: FSMContext
):

    limitations = message.text

    try:
        await message.delete()
    except Exception:
        pass

    data = await state.get_data()

    limitations_message_id = data.get("limitations_message_id")

    if limitations_message_id:

        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=limitations_message_id
            )
        except Exception:
            pass

    await state.update_data(
        limitations=limitations
    )

    data = await state.get_data()

    profile = get_user_profile(
        message.from_user.id
    )

    loading_message = await message.answer(
    "🤖 <b>Создаю персональный план...</b>\n\n"

    "📊 Анализирую профиль\n"
    "🎯 Подбираю упражнения под цель\n"
    "🏋️ Учитываю уровень подготовки\n"
    "⚠️ Проверяю ограничения\n"
    "📈 Формирую прогрессию нагрузки\n\n"

    "Это может занять несколько секунд...",
    parse_mode="HTML"
    )

    try:

        response = client.responses.create(
            model="gpt-4.1-mini",
            input=(
                "Ты профессиональный фитнес-тренер Gym AI.\n"
                "Создай персональный план тренировок на русском языке.\n\n"

                "ДАННЫЕ ПОЛЬЗОВАТЕЛЯ:\n"
                f"Профиль пользователя: {profile}\n"
                f"Цель: {data['goal']}\n"
                f"Места тренировок: {', '.join(data['locations'])}\n"
                f"Уровень: {data['level']}\n"
                f"Тренировок в неделю: {data['workouts_per_week']}\n"
                f"Рабочие веса: {data.get('working_weights', 'не указано')}\n"
                f"Фокус тренировок: {data.get('focus', 'Баланс всего тела')}\n"
                f"Ограничения: {data['limitations']}\n\n"

                "ТРЕБОВАНИЯ:\n"
                "- учитывай пол пользователя из профиля, если он указан\n"
                "- не используй стереотипы\n"
                "- план должен зависеть от цели, уровня, профиля, фокуса и рабочих весов\n"
                "- если указаны рабочие веса — предложи примерные веса для подходов\n"
                "- если рабочих весов нет — дай безопасные ориентиры\n"
                "- веса должны быть примерными и безопасными\n"
                "- если техника ломается — рекомендовать снизить вес\n"
                "- добавь прогрессию силовых на 4 недели\n"
                "- распиши как увеличивать вес, подходы или повторы\n"
                "- учитывай ограничения пользователя\n"
                "- план должен быть реалистичным\n"
                "- упражнения должны соответствовать месту тренировок\n\n"

                "ФОРМАТ ОТВЕТА:\n\n"
                "🔥 <b>ПЛАН ТРЕНИРОВОК GYM AI</b>\n\n"

                "Раздели план по тренировочным дням.\n\n"

                "Для каждого упражнения укажи:\n"
                "- подходы\n"
                "- повторения\n"
                "- примерный вес\n"
                "- отдых между подходами\n\n"

                "📈 <b>ПРОГРЕССИЯ НА 4 НЕДЕЛИ</b>\n"
                "Неделя 1: ...\n"
                "Неделя 2: ...\n"
                "Неделя 3: ...\n"
                "Неделя 4: ...\n\n"

                "🎯 <b>РЕКОМЕНДАЦИИ GYM AI</b>\n"
                "- восстановление\n"
                "- кардио\n"
                "- сон\n"
                "- питание\n\n"
                
                "Не используй теги <br>, <ul>, <li>, <p>. Только <b>.\n"
                "Не используй Markdown. Используй только HTML <b>."
                
            )
        )
    
        workout_plan = response.output_text

        workout_plan = (
            workout_plan
                .replace("<br>", "\n")
                .replace("<br/>", "\n")
                .replace("<br />", "\n")
        )
    
    except Exception as e:

        print("WORKOUT PLAN ERROR:", e)

        try:
            await loading_message.delete()
        except Exception:
            pass

        await message.answer(
            "⚠️ Не удалось создать план тренировок.\n\n"
            "Попробуй еще раз через пару секунд.",
            parse_mode="HTML"
        )

        await state.clear()
        return

    try:
        await loading_message.delete()
    except Exception:
        pass

    save_workout_plan(
        message.from_user.id,
        {
            "goal": data["goal"],
            "locations": data["locations"],
            "level": data["level"],
            "workouts_per_week": data["workouts_per_week"],
            "working_weights": data.get("working_weights", "не указано"),
            "focus": data.get("focus", "Баланс всего тела"),
            "limitations": data["limitations"],
            "plan_text": workout_plan,
        }
    )

    await message.answer(
        workout_plan,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="▶️ Начать тренировку",
                        callback_data="start_workout_from_plan"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔄 Создать новый план",
                        callback_data="create_workout_plan"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🏠 Главное меню",
                        callback_data="back_to_main_menu"
                    )
                ],
            ]
        ),
        parse_mode="HTML"
    )

    await state.clear()


# ==========================================
#          ВЫБОР ЦЕЛИ
# ==========================================

@router.callback_query(
    F.data.startswith("goal_")
)
async def workout_goal_handler(
    callback: CallbackQuery,
    state: FSMContext
):

    goal_map = {

        "goal_mass": "Набор массы",

        "goal_weight_loss": "Похудение",

        "goal_maintenance": "Поддержание формы",
    }

    goal = goal_map.get(callback.data)

    await state.update_data(
        goal=goal
    )

    keyboard = workout_locations_keyboard()

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        "📍 <b>Где ты тренируешься?</b>\n\n"
        "Можно выбрать несколько вариантов 👇",

        reply_markup=keyboard,

        parse_mode="HTML"
    )

    await state.set_state(
        CreateWorkoutPlan.location
    )

    await callback.answer()


# ==========================================
#              МОЙ ПЛАН
# ==========================================

@router.callback_query(F.data == "my_workout_plan")
async def my_workout_plan_handler(callback: CallbackQuery):

    try:
        await callback.message.delete()
    except Exception:
        pass

    is_premium = get_premium_status(
        callback.from_user.id
    )

    advanced_plan_button_text = (
        "🧠 Продвинутый AI план"
        if is_premium
        else "💎 Продвинутый AI план"
    )

    plan = get_workout_plan(
        callback.from_user.id
    )

    if not plan:

        await callback.message.answer(
            "📋 <b>Мой план тренировок</b>\n\n"
            "У тебя пока нет тренировочного плана.\n\n"
            "Создай базовый план бесплатно или открой продвинутый AI план в Premium.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="➕ Создать план",
                            callback_data="create_workout_plan_free"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text=advanced_plan_button_text,
                            callback_data="create_workout_plan"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="⬅️ Назад",
                            callback_data="menu_workout"
                        )
                    ],
                ]
            ),
            parse_mode="HTML"
        )

        await callback.answer()
        return

    plan_type = plan.get("type", "premium")

    if plan_type == "free":
        plan_type_text = "🆓 Базовый план"
    else:
        plan_type_text = "💎 Продвинутый AI план"

    locations = plan.get("locations", [])

    if isinstance(locations, list):
        locations_text = ", ".join(locations)
    else:
        locations_text = locations

    header_text = (
        "📋 <b>ТВОЙ ПЛАН ТРЕНИРОВОК</b>\n\n"

        f"🎯 Цель: <b>{plan.get('goal', '—')}</b>\n"
        f"📅 Частота: <b>{plan.get('workouts_per_week', '—')} раз/нед.</b>\n"
        f"📍 Место: <b>{locations_text or '—'}</b>\n"
        f"🏋️ Уровень: <b>{plan.get('level', '—')}</b>\n"
        f"💎 Тип плана: <b>{plan_type_text}</b>\n\n"

        "━━━━━━━━━━━━━━\n\n"
    )

    await callback.message.answer(
        header_text + plan["plan_text"],
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="▶️ Начать тренировку",
                        callback_data="start_workout_from_plan"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="➕ Создать базовый план",
                        callback_data="create_workout_plan_free"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=advanced_plan_button_text,
                        callback_data="create_workout_plan"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🗑 Удалить план",
                        callback_data="delete_workout_plan"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ Назад",
                        callback_data="menu_workout"
                    )
                ],
            ]
        ),
        parse_mode="HTML"
    )

    await callback.answer()


# ==========================================
#          СТАРТ ЗАПИСИ ТРЕНИРОВКИ
# ==========================================

@router.callback_query(F.data == "log_workout")
async def start_log_workout(
    callback: CallbackQuery,
    state: FSMContext
):

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        "💪 <b>Записать тренировку</b>\n\n"
        "Напиши, что ты сделал на тренировке.\n\n"
        "<i>Например:\n"
        "Жим лежа 80 кг × 8 повторений × 3 подхода\n"
        "Присед 100 кг × 5 повторений × 4 подхода</i>",
        parse_mode="HTML"
    )

    await state.set_state(
        LogWorkoutForm.workout_text
    )

    await callback.answer()


# ==========================================
#          ОБРАБОТКА ЗАПИСИ ТРЕНИРОВКИ
# ==========================================

@router.message(LogWorkoutForm.workout_text)
async def process_log_workout(
    message: Message,
    state: FSMContext
):

    if len(message.text.strip()) < 3:

        await message.answer(
            "Опиши тренировку чуть подробнее."
        )

        return

    workout_text = message.text

    try:
        await message.delete()
    except Exception:
        pass

    loading_message = await message.answer(
        "🤖 <b>Обрабатываю тренировку...</b>\n\n"
        "Привожу запись в красивый формат 💪",
        parse_mode="HTML"
    )

    try:

        response = client.responses.create(
            model="gpt-4.1-mini",
            input=(
                "Ты фитнес-тренер в Telegram-боте Gym AI.\n"
                "Пользователь записывает выполненную тренировку.\n"
                "Оформи тренировку красиво на русском языке.\n\n"

                f"Запись пользователя: {workout_text}\n\n"

                "Формат ответа:\n\n"
                "💪 <b>ТРЕНИРОВКА ЗАПИСАНА</b>\n\n"
                "📌 <b>Упражнения</b>\n"
                "1. Упражнение — вес × повторы × подходы\n"
                "2. Упражнение — вес × повторы × подходы\n\n"
                "📊 <b>Краткий итог</b>\n"
                "• Основная группа мышц: ...\n"
                "• Интенсивность: ...\n"
                "• Комментарий: ...\n\n"
                "Не используй Markdown. Используй только HTML <b>."
            )
        )

    except Exception as e:

        print("OPENAI WORKOUT LOG ERROR:", e)

        try:
            await loading_message.delete()
        except Exception:
            pass

        await message.answer(
            "⚠️ Не получилось обработать тренировку.\n\n"
            "Попробуй ещё раз через пару секунд.",
            reply_markup=workout_menu_keyboard(),
            parse_mode="HTML"
        )

        await state.clear()
        return

    try:
        await loading_message.delete()
    except Exception:
        pass

    add_workout_history_entry(
        message.from_user.id,
        {
            "date": str(date.today()),
            "text": response.output_text,
            "raw_text": workout_text,
        }
    )

    await message.answer(
        response.output_text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔥 История тренировок",
                        callback_data="workout_history"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ Назад в тренировки",
                        callback_data="menu_workout"
                    )
                ],
            ]
        ),
        parse_mode="HTML"
    )

    await state.clear()


# ==========================================
#      КЛАВИАТУРА УДАЛЕНИЯ ТРЕНИРОВКИ
# ==========================================

def delete_workout_keyboard(history):

    buttons = []

    for index, workout in enumerate(history, start=1):

        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"🗑 {index}. {workout['date']}",
                    callback_data=f"delete_workout_{index - 1}"
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="workout_history"
            )
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


# ==========================================
#      КЛАВИАТУРА ИСТОРИИ ТРЕНИРОВОК
# ==========================================

def workout_history_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📅 Сегодня",
                    callback_data="workout_history_today"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📅 Вчера",
                    callback_data="workout_history_yesterday"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📆 Все тренировки",
                    callback_data="workout_history_all"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="menu_workout"
                )
            ],
        ]
    )

# ==========================================
#     КЛАВИАТУРА ИСТОРИИ И ПРОГРЕССА
# ==========================================

def workout_stats_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔥 История тренировок",
                    callback_data="workout_history"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📈 Анализ прогресса",
                    callback_data="workout_progress"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="menu_workout"
                )
            ],
        ]
    )


# ==========================================
#       МЕНЮ ИСТОРИИ И ПРОГРЕССА
# ==========================================

@router.callback_query(F.data == "workout_stats")
async def workout_stats_handler(callback: CallbackQuery):

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        "📊 <b>Статистика тренировок</b>\n\n"
        "Выбери нужный раздел:",
        reply_markup=workout_stats_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()

# ==========================================
#          ИСТОРИЯ ТРЕНИРОВОК
# ==========================================

@router.callback_query(F.data == "workout_history")
async def workout_history_handler(callback: CallbackQuery):

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        "🔥 <b>История тренировок</b>\n\n"
        "Выбери период:",
        reply_markup=workout_history_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()

async def show_workout_history(
    callback: CallbackQuery,
    filter_date=None
    ):

        try:
            await callback.message.delete()
        except Exception:
            pass

        history = get_workout_history(
            callback.from_user.id
        )

        if filter_date:
            history = [
                workout for workout in history
                if workout.get("date") == filter_date
            ]

        if not history:

            await callback.message.answer(
            "🔥 <b>История тренировок</b>\n\n"
            "За этот период тренировок пока нет.",
            reply_markup=workout_history_keyboard(),
            parse_mode="HTML"
            )

            await callback.answer()
            return

        text = "🔥 <b>История тренировок</b>\n\n"

        for index, workout in enumerate(history, start=1):

            text += (
            f"📅 <b>{workout['date']}</b>\n"
            f"{workout['text']}\n\n"
            )

        await callback.message.answer(
            text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🗑 Удалить тренировку",
                        callback_data="delete_workout"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ Назад",
                        callback_data="workout_history"
                    )
                ],
                ]
            ),
            parse_mode="HTML"
        )

        await callback.answer()


# ==========================================
#     ОБРАБОТЧИК ИСТОРИи ТРЕНИРОВОК
# ==========================================

@router.callback_query(F.data == "workout_history_today")
async def workout_history_today_handler(callback: CallbackQuery):

    await show_workout_history(
        callback,
        str(date.today())
    )


@router.callback_query(F.data == "workout_history_yesterday")
async def workout_history_yesterday_handler(callback: CallbackQuery):

    yesterday = date.today() - timedelta(days=1)

    await show_workout_history(
        callback,
        str(yesterday)
    )


@router.callback_query(F.data == "workout_history_all")
async def workout_history_all_handler(callback: CallbackQuery):

    await show_workout_history(callback)


# ==========================================
#          ПРОГРЕСС ТРЕНИРОВОК
# ==========================================

@router.callback_query(F.data == "workout_progress")
async def workout_progress_handler(callback: CallbackQuery):

    try:
        await callback.message.delete()
    except Exception:
        pass

    history = get_workout_history(
        callback.from_user.id
    )

    if not history:

        await callback.message.answer(
            "📊 <b>Прогресс тренировок</b>\n\n"
            "Пока нет записанных тренировок.\n\n"
            "Запиши первую тренировку, чтобы здесь появилась статистика.",
            reply_markup=workout_menu_keyboard(),
            parse_mode="HTML"
        )

        await callback.answer()
        return

    total_workouts = len(history)

    last_workout = history[-1]

    unique_dates = set(
        workout.get("date")
        for workout in history
    )

    training_days = len(unique_dates)

    recent_workouts = history[-5:]

    workout_texts = "\n\n".join(
        workout.get("text", "")
        for workout in recent_workouts
    )

    loading_message = await callback.message.answer(
        "🤖 <b>Анализирую твой тренировочный прогресс...</b>\n\n"
        "Смотрю последние тренировки и общую активность 📊",
        parse_mode="HTML"
    )

    try:

        response = client.responses.create(
            model="gpt-4.1-mini",
            input=(
                "Ты AI-фитнес тренер в Telegram-боте Gym AI.\n"
                "Проанализируй тренировочный прогресс пользователя на русском языке.\n\n"

                "СТАТИСТИКА:\n"
                f"Всего тренировок: {total_workouts}\n"
                f"Тренировочных дней: {training_days}\n"
                f"Последняя тренировка: {last_workout['date']}\n\n"

                "ПОСЛЕДНИЕ ТРЕНИРОВКИ:\n"
                f"{workout_texts}\n\n"

                "Дай короткий, полезный и мотивирующий анализ.\n"
                "Формат:\n\n"
                "📊 <b>ПРОГРЕСС ТРЕНИРОВОК</b>\n\n"
                "🏋️ Всего тренировок: ...\n"
                "📅 Тренировочных дней: ...\n"
                "🔥 Последняя тренировка: ...\n\n"
                "🤖 <b>Анализ Gym AI</b>\n"
                "...\n\n"
                "✅ <b>Рекомендации</b>\n"
                "• ...\n"
                "• ...\n"
                "• ...\n\n"
                "Не используй Markdown. Используй HTML <b>."
            )
        )

    except Exception as e:

        print("OPENAI WORKOUT PROGRESS ERROR:", e)

        try:
            await loading_message.delete()
        except Exception:
            pass

        await callback.message.answer(
            "📊 <b>Прогресс тренировок</b>\n\n"
            f"🏋️ Всего тренировок: <b>{total_workouts}</b>\n"
            f"📅 Тренировочных дней: <b>{training_days}</b>\n"
            f"🔥 Последняя тренировка: <b>{last_workout['date']}</b>\n\n"
            "Gym AI не смог сделать анализ сейчас, но статистика сохранена.",
            reply_markup=workout_menu_keyboard(),
            parse_mode="HTML"
        )

        await callback.answer()
        return

    try:
        await loading_message.delete()
    except Exception:
        pass

    await callback.message.answer(
        response.output_text,
        reply_markup=workout_menu_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


# ==========================================
#          УДАЛЕНИЕ ТРЕНИРОВКИ
# ==========================================

@router.callback_query(F.data == "delete_workout")
async def delete_workout_handler(callback: CallbackQuery):

    try:
        await callback.message.delete()
    except Exception:
        pass

    history = get_workout_history(
        callback.from_user.id
    )

    if not history:

        await callback.message.answer(
            "❌ История тренировок пустая.",
            reply_markup=workout_menu_keyboard(),
            parse_mode="HTML"
        )

        await callback.answer()
        return

    await callback.message.answer(
        "🗑 <b>Удаление тренировки</b>\n\n"
        "Выбери тренировку, которую нужно удалить:",
        reply_markup=delete_workout_keyboard(history),
        parse_mode="HTML"
    )

    await callback.answer()


# ==========================================
#       УДАЛЕНИЕ ТРЕНИРОВКИ ПО КНОПКЕ
# ==========================================

@router.callback_query(F.data.startswith("delete_workout_"))
async def delete_workout_by_button(callback: CallbackQuery):

    index = int(
        callback.data.replace("delete_workout_", "")
    )

    success = delete_workout_history_entry(
        callback.from_user.id,
        index
    )

    try:
        await callback.message.delete()
    except Exception:
        pass

    if success:

        await callback.answer("Тренировка удалена")

        await workout_history_handler(callback)

    else:

        await callback.message.answer(
            "❌ Не удалось удалить тренировку.",
            reply_markup=workout_menu_keyboard(),
            parse_mode="HTML"
        )

        await callback.answer()


# ==========================================
#       ПОЛУЧЕНИЕ ДНЕЙ ПЛАНА ПОЛНОСТЬЮ
# ==========================================

def extract_workout_days(plan_text):

    lines = plan_text.split("\n")

    workout_days = []
    current_day = []

    for line in lines:

        clean_line = (
            line.replace("<b>", "")
                .replace("</b>", "")
                .strip()
        )

        if "ДЕНЬ" in clean_line.upper():

            if current_day:
                workout_days.append("\n".join(current_day).strip())

            current_day = [clean_line]

        else:

            if current_day:
                current_day.append(line.strip())

    if current_day:
        workout_days.append("\n".join(current_day).strip())

    return workout_days


# ==========================================
#          НАЧАТЬ ТРЕНИРОВКУ ИЗ ПЛАНА
# ==========================================

@router.callback_query(F.data == "start_workout_from_plan")
async def start_workout_from_plan(callback: CallbackQuery):

    try:
        await callback.message.delete()
    except Exception:
        pass

    plan = get_workout_plan(
        callback.from_user.id
    )

    if not plan:

        await callback.message.answer(
            "❌ У тебя пока нет тренировочного плана.",
            reply_markup=workout_menu_keyboard(),
            parse_mode="HTML"
        )

        await callback.answer()
        return

    workout_days = extract_workout_days(
        plan["plan_text"]
    )

    if not workout_days:

        workout_days = [
            "🔥 Тренировка"
        ]

    buttons = []

    for index, day in enumerate(workout_days):

        buttons.append(
            [
                InlineKeyboardButton(
                    text=day.split("\n")[0][:40],
                    callback_data=f"start_day_{index}"
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="my_workout_plan"
            )
        ]
    )

    await callback.message.answer(
        "▶️ <b>Выбери тренировочный день</b>\n\n"
        "Какую тренировку начинаем?",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
        parse_mode="HTML"
    )

    await callback.answer()


# ==========================================
#      КЛАВИАТУРА ОЦЕНКИ ТРЕНИРОВКИ
# ==========================================

def workout_feeling_keyboard(day_index):

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="😴 Легко",
                    callback_data=f"workout_feeling_easy_{day_index}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔥 Нормально",
                    callback_data=f"workout_feeling_normal_{day_index}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💀 Тяжело",
                    callback_data=f"workout_feeling_hard_{day_index}"
                )
            ],
        ]
    )


# ==========================================
#        ЗАВЕРШЕНИЕ ТРЕНИРОВКИ
# ==========================================

@router.callback_query(F.data.startswith("finish_day_"))
async def finish_workout_day(callback: CallbackQuery):

    index = int(
        callback.data.replace(
            "finish_day_",
            ""
        )
    )

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        "✅ <b>Тренировка завершена</b>\n\n"
        "Как прошла тренировка?",
        reply_markup=workout_feeling_keyboard(index),
        parse_mode="HTML"
    )

    await callback.answer()



# ==========================================
#         ЗАПУСК ТРЕНИРОВОЧНОГО ДНЯ
# ==========================================

@router.callback_query(F.data.startswith("start_day_"))
async def start_workout_day(callback: CallbackQuery):

    index = int(
        callback.data.replace(
            "start_day_",
            ""
        )
    )

    plan = get_workout_plan(
        callback.from_user.id
    )

    if not plan:

        await callback.answer(
            "План не найден",
            show_alert=True
        )

        return

    workout_days = extract_workout_days(
        plan["plan_text"]
    )

    selected_day = workout_days[index]

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
    "🏋️ <b>ТРЕНИРОВКА НАЧАЛАСЬ</b>\n\n"

    "Сегодня работаем по выбранному тренировочному дню.\n\n"

    "━━━━━━━━━━━━━━\n\n"

    f"{selected_day}\n\n"

    "━━━━━━━━━━━━━━\n\n"

    "💡 <b>Совет Gym AI</b>\n"
    "Следи за техникой выполнения и качеством каждого подхода.\n\n"

    "Когда закончишь тренировку — нажми кнопку ниже 👇",

        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Завершить тренировку",
                        callback_data=f"finish_day_{index}"
                    )
                ],
                [
                    InlineKeyboardButton(
                    text="❌ Отменить тренировку",
                    callback_data="cancel_started_workout"
                    )
                ],
            ]
        ),

        parse_mode="HTML"
    )

    await callback.answer()


# ==========================================
#          ОТМЕНА НАЧАТОЙ ТРЕНИРОВКИ
# ==========================================

@router.callback_query(F.data == "cancel_started_workout")
async def cancel_started_workout(callback: CallbackQuery):

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        "❌ <b>Тренировка отменена</b>\n\n"
        "Ничего не сохранено в историю.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="▶️ Выбрать другой день",
                        callback_data="start_workout_from_plan"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ Назад в тренировки",
                        callback_data="menu_workout"
                    )
                ],
            ]
        ),
        parse_mode="HTML"
    )

    await callback.answer()


# ==========================================
#        СОХРАНЕНИЕ ТРЕНИРОВКИ С ОЦЕНКОЙ
# ==========================================

@router.callback_query(F.data.startswith("workout_feeling_"))
async def save_workout_with_feeling(callback: CallbackQuery):

    data = callback.data.replace("workout_feeling_", "")

    parts = data.rsplit("_", 1)

    feeling = parts[0]
    index = int(parts[1])

    feeling_map = {
        "easy": "😴 Легко",
        "normal": "🔥 Нормально",
        "hard": "💀 Тяжело",
    }

    plan = get_workout_plan(
        callback.from_user.id
    )

    if not plan:

        await callback.answer(
            "План не найден",
            show_alert=True
        )

        return

    workout_days = extract_workout_days(
        plan["plan_text"]
    )

    selected_day = workout_days[index]

    add_workout_history_entry(
        callback.from_user.id,
        {
            "date": str(date.today()),
            "text": (
                "✅ <b>ТРЕНИРОВКА ВЫПОЛНЕНА</b>\n\n"
                f"{selected_day}\n\n"
                f"Самочувствие: <b>{feeling_map.get(feeling, feeling)}</b>"
            ),
            "raw_text": selected_day,
            "feeling": feeling,
        }
    )

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
    "✅ <b>ТРЕНИРОВКА СОХРАНЕНА</b>\n\n"

    "🏋️ Отличная работа!\n\n"

    f"Самочувствие: <b>{feeling_map.get(feeling, feeling)}</b>\n\n"

    "📈 Запись добавлена в историю тренировок.\n"
    "🤖 Gym AI будет учитывать эту тренировку при анализе прогресса.\n\n"

    "Продолжай двигаться к своей цели 💪",
    reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 История и прогресс",
                    callback_data="workout_stats"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏋️ К тренировкам",
                    callback_data="menu_workout"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data="back_to_main_menu"
                )
            ],
        ]
    ),
    parse_mode="HTML"
    )

    await callback.answer()


# ==========================================
#         AI АНАЛИЗ ТРЕНИРОВОК
# ==========================================

@router.callback_query(F.data == "ai_workout_analysis")
async def ai_workout_analysis_handler(callback: CallbackQuery):

    try:
        await callback.message.delete()
    except Exception:
        pass

    # PREMIUM ПРОВЕРКА

    is_premium = get_premium_status(
        callback.from_user.id
    )

    if not is_premium:

        await callback.message.answer(
            "💎 <b>AI анализ тренировок доступен в Premium</b>\n\n"

            "Premium откроет:\n"
            "• анализ тренировочной нагрузки\n"
            "• оценку прогресса\n"
            "• поиск слабых мест\n"
            "• рекомендации Gym AI\n"
            "• персональные советы по тренировкам\n\n"

            "Чтобы открыть функцию — активируй Premium.",

            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="💎 Открыть Premium",
                            callback_data="subscription"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🏋️ Назад к тренировкам",
                            callback_data="menu_workout"
                        )
                    ],
                ]
            ),
            parse_mode="HTML"
        )

        await callback.answer()
        return

    profile = get_user_profile(
        callback.from_user.id
    )

    plan = get_workout_plan(
        callback.from_user.id
    )

    history = get_workout_history(
        callback.from_user.id
    )

    if not history:

        await callback.message.answer(
            "📊 <b>Недостаточно данных</b>\n\n"

            "Для AI анализа нужно записать хотя бы одну тренировку.",

            reply_markup=workout_menu_keyboard(),
            parse_mode="HTML"
        )

        await callback.answer()
        return

    recent_workouts = history[-5:]

    loading_message = await callback.message.answer(
        "🤖 <b>Gym AI анализирует тренировки...</b>\n\n"
        "Изучаю план, историю и тренировочную нагрузку.",
        parse_mode="HTML"
    )

    try:

        response = client.responses.create(
            model="gpt-4.1-mini",
            input=(
                "Ты профессиональный фитнес-тренер Gym AI.\n"
                "Сделай глубокий анализ тренировок пользователя.\n\n"

                "ТВОЯ ЗАДАЧА:\n"
                "Оцени тренировочный процесс пользователя.\n"
                "Проанализируй регулярность тренировок, нагрузку, прогресс и самочувствие.\n"
                "Дай практические рекомендации.\n\n"

                "ДАННЫЕ ПОЛЬЗОВАТЕЛЯ:\n"
                f"Профиль: {profile}\n\n"

                f"Текущий план: {plan}\n\n"

                f"Последние тренировки: {recent_workouts}\n\n"

                "ФОРМАТ ОТВЕТА:\n\n"

                "🏋️ <b>AI анализ тренировок</b>\n\n"

                "📊 <b>Общая оценка</b>\n"
                "Коротко оцени тренировочную ситуацию.\n\n"

                "✅ <b>Что хорошо</b>\n"
                "• ...\n"
                "• ...\n\n"

                "⚠️ <b>Что тормозит прогресс</b>\n"
                "• ...\n"
                "• ...\n\n"

                "📈 <b>Нагрузка</b>\n"
                "Оцени уровень нагрузки и восстановление.\n\n"

                "🎯 <b>Что делать дальше</b>\n"
                "• ...\n"
                "• ...\n"
                "• ...\n\n"

                "💡 <b>Совет Gym AI</b>\n"
                "Один конкретный совет.\n\n"

                "Пиши коротко, понятно и по делу.\n"
                "Не используй Markdown.\n"
                "Используй только HTML <b>."
            )
        )

    except Exception as e:

        print("AI WORKOUT ANALYSIS ERROR:", e)

        try:
            await loading_message.delete()
        except Exception:
            pass

        await callback.message.answer(
            "⚠️ <b>AI анализ временно недоступен</b>\n\n"
            "Попробуй ещё раз через пару секунд.",
            reply_markup=workout_menu_keyboard(),
            parse_mode="HTML"
        )

        await callback.answer()
        return

    try:
        await loading_message.delete()
    except Exception:
        pass

    result_text = (
        response.output_text
        .replace("<br>", "\n")
        .replace("<br/>", "\n")
        .replace("<br />", "\n")
    )

    await callback.message.answer(
        result_text,
        reply_markup=workout_menu_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()