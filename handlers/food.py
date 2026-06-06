# ==========================================
#               ИМПОРТЫ
# ==========================================

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from handlers.menu import food_menu_keyboard

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from openai import OpenAI
from config import OPENAI_API_KEY
from storage import (
    save_user_kbju,
    get_user_kbju,
    add_food_diary_entry,
    get_food_diary,
    delete_food_diary_entry,
    add_water_entry,
    get_water_amount,
    remove_water_entry,
    get_premium_status,
)

import re
from datetime import date, timedelta

# ==========================================
#            OPENAI CLIENT
# ==========================================

client = OpenAI(
    api_key=OPENAI_API_KEY,
    timeout=60
)


# ==========================================
#            СОЗДАНИЕ ROUTER
# ==========================================

router = Router()


# ==========================================
#        СОСТОЯНИЯ РАСЧЕТА КБЖУ
# ==========================================

class FoodKbjuForm(StatesGroup):

    # ПОЛ
    gender = State()

    # ВОЗРАСТ
    age = State()

    # РОСТ
    height = State()

    # ВЕС
    weight = State()

    # ЦЕЛЬ
    goal = State()

    # АКТИВНОСТЬ
    activity = State()

    # ТЕМП
    speed = State()


# ==========================================
#        СОСТОЯНИЯ МЕНЮ НА ДЕНЬ
# ==========================================

class DailyMenuForm(StatesGroup):

    # РАЗРЕШЕННЫЕ ПРОДУКТЫ
    allowed_products = State()

    # ЗАПРЕЩЕННЫЕ ПРОДУКТЫ
    forbidden_products = State()

    # КОЛИЧЕСТВО ПРИЕМОВ ПИЩИ
    meals_count = State()

# ==========================================
#        СОСТОЯНИЯ ЗАПИСИ БЛЮДА
# ==========================================

class AddMealForm(StatesGroup):

    # ПРИЕМ ПИЩИ
    meal_type = State()

    # ОПИСАНИЕ БЛЮДА
    meal_text = State()

    # УДАЛЕНИЕ БЛЮДА
    delete_meal = State()


# ==========================================
#        КЛАВИАТУРА ВЫБОРА ПОЛА
# ==========================================

def gender_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Мужчина",
                    callback_data="food_gender_male"
                ),
                InlineKeyboardButton(
                    text="Женщина",
                    callback_data="food_gender_female"
                ),
            ]
        ]
    )


# ==========================================
#        КЛАВИАТУРА ВЫБОРА ЦЕЛИ
# ==========================================

def goal_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Похудение",
                    callback_data="food_goal_loss"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Поддержание формы",
                    callback_data="food_goal_maintain"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Набор массы",
                    callback_data="food_goal_gain"
                )
            ],
        ]
    )


# ==========================================
#      КЛАВИАТУРА ВЫБОРА АКТИВНОСТИ
# ==========================================

def activity_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛋 Сижу дома, ничего не делаю",
                    callback_data="food_activity_low"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🚶 Легкая активность 1–2 раза в неделю",
                    callback_data="food_activity_light"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏃 Средняя активность 3–4 раза в неделю",
                    callback_data="food_activity_medium"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏋️ Высокая активность 5–7 раз в неделю",
                    callback_data="food_activity_high"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💪 Физическая работа + спорт",
                    callback_data="food_activity_very_high"
                )
            ],
        ]
    )


# ==========================================
#      КЛАВИАТУРА ТЕМПА ИЗМЕНЕНИЯ ТЕЛА
# ==========================================

def speed_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🐢 Плавно",
                    callback_data="food_speed_slow"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚡ Умеренно",
                    callback_data="food_speed_medium"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔥 Быстро",
                    callback_data="food_speed_fast"
                )
            ],
            [
                InlineKeyboardButton(
                    text="☠️ Экстремальная весогонка",
                    callback_data="food_speed_extreme"
                )
            ],
        ]
    )


# ==========================================
#      КЛАВИАТУРА ПОСЛЕ РЕЗУЛЬТАТА
# ==========================================

# ==========================================
#      КЛАВИАТУРА ПОСЛЕ РАСЧЕТА КБЖУ
# ==========================================

def kbju_result_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            # МЕНЮ НА ДЕНЬ
            [
                InlineKeyboardButton(
                    text="🍱 Меню на день",
                    callback_data="food_daily_menu"
                )
            ],

            # ПЕРЕСЧИТАТЬ КБЖУ
            [
                InlineKeyboardButton(
                    text="🔁 Рассчитать заново",
                    callback_data="food_calculate_kbju"
                )
            ],

            # НАЗАД В ПИТАНИЕ
            [
                InlineKeyboardButton(
                    text="⬅️ Назад в питание",
                    callback_data="menu_food"
                )
            ],
        ]
    )


# ==========================================
#        УДАЛЕНИЕ ПОСЛЕДНЕГО ВОПРОСА
# ==========================================

async def delete_last_bot_message(
    message_or_callback,
    state: FSMContext
):

    data = await state.get_data()
    last_bot_message_id = data.get("last_bot_message_id")

    if last_bot_message_id:

        try:

            if isinstance(message_or_callback, CallbackQuery):
                chat_id = message_or_callback.message.chat.id
                bot = message_or_callback.bot
            else:
                chat_id = message_or_callback.chat.id
                bot = message_or_callback.bot

            await bot.delete_message(
                chat_id=chat_id,
                message_id=last_bot_message_id
            )

        except Exception:

            pass


# ==========================================
#              РАСЧЕТ КБЖУ
# ==========================================

def calculate_kbju(
    age,
    gender,
    height,
    weight,
    goal,
    activity,
    speed
):

    age = int(age)
    height = int(height)
    weight = float(weight)

    # БАЗОВЫЙ ОБМЕН ПО ФОРМУЛЕ MIFFLIN-ST JEOR
    if gender == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    activity_map = {
        "low": 1.2,
        "light": 1.375,
        "medium": 1.55,
        "high": 1.725,
        "very_high": 1.9,
    }

    speed_map = {
        "slow": 200,
        "medium": 350,
        "fast": 500,
        "extreme": 700,
    }

    activity_coef = activity_map.get(activity, 1.375)
    correction = speed_map.get(speed, 350)

    maintenance_calories = bmr * activity_coef

    if goal == "loss":
        calories = maintenance_calories - correction
        protein = weight * 2.0
        fat = weight * 0.8

    elif goal == "gain":
        calories = maintenance_calories + correction
        protein = weight * 1.8
        fat = weight * 1.0

    else:
        calories = maintenance_calories
        protein = weight * 1.8
        fat = weight * 0.9

    # ЗАЩИТА ОТ СЛИШКОМ НИЗКИХ КАЛОРИЙ
    min_calories = bmr * 1.15

    if calories < min_calories:
        calories = min_calories

    carbs = (calories - protein * 4 - fat * 9) / 4

    if carbs < 80:
        carbs = 80
        calories = protein * 4 + fat * 9 + carbs * 4

    return {
        "calories": round(calories),
        "protein": round(protein),
        "fat": round(fat),
        "carbs": round(carbs),
        "bmr": round(bmr),
        "maintenance": round(maintenance_calories),
    }


# ==========================================
#          СТАРТ РАСЧЕТА КБЖУ
# ==========================================

@router.callback_query(F.data == "food_calculate_kbju")
async def start_food_kbju(
    callback: CallbackQuery,
    state: FSMContext
):

    try:
        await callback.message.delete()
    except Exception:
        pass

    question = await callback.message.answer(
        "🔥 <b>Расчёт КБЖУ</b>\n\n"
        "Gym AI рассчитает твою дневную норму калорий, белков, жиров и углеводов.\n\n"
        "Сначала укажи пол:",
        reply_markup=gender_keyboard(),
        parse_mode="HTML"
    )

    await state.update_data(
        last_bot_message_id=question.message_id
    )

    await state.set_state(
        FoodKbjuForm.gender
    )

    await callback.answer()


# ==========================================
#             ОБРАБОТКА ПОЛА
# ==========================================

@router.callback_query(
    FoodKbjuForm.gender,
    F.data.startswith("food_gender_")
)
async def process_food_gender(
    callback: CallbackQuery,
    state: FSMContext
):

    try:
        await callback.message.delete()
    except Exception:
        pass

    gender = callback.data.replace("food_gender_", "")

    await state.update_data(
        gender=gender
    )

    question = await callback.message.answer(
        "🎂 <b>Возраст</b>\n\n"
        "Сколько тебе полных лет? <i>Например: 25</i>",
        parse_mode="HTML"
    )

    await state.update_data(
        last_bot_message_id=question.message_id
    )

    await state.set_state(
        FoodKbjuForm.age
    )

    await callback.answer()


# ==========================================
#             ОБРАБОТКА ВОЗРАСТА
# ==========================================

@router.message(FoodKbjuForm.age)
async def process_food_age(
    message: Message,
    state: FSMContext
):

    if not message.text.isdigit():

        await message.answer(
            "⚠️ Введи возраст числом.\n\n"
            "Например: 25"
        )

        return

    age = int(message.text)

    if age < 10 or age > 100:

        await message.answer(
            "⚠️ Укажи реальный возраст.\n\n"
            "Например: 25"
        )

        return

    await delete_last_bot_message(message, state)
    
    try:
        await message.delete()
    except Exception:
        pass

    await state.update_data(
        age=age
    )

    question = await message.answer(
        "📏 <b>Рост</b>\n\n"
        "Укажи свой рост в сантиметрах:\n"
        "<i>Например: 180</i>",
        parse_mode="HTML"
    )

    await state.update_data(
        last_bot_message_id=question.message_id
    )

    await state.set_state(
        FoodKbjuForm.height
    )


# ==========================================
#             ОБРАБОТКА РОСТА
# ==========================================

@router.message(FoodKbjuForm.height)
async def process_food_height(
    message: Message,
    state: FSMContext
):

    if not message.text.isdigit():

        await message.answer(
            "⚠️ Введи рост числом.\n\n"
            "Например: 180"
        )

        return

    height = int(message.text)

    if height < 100 or height > 230:

        await message.answer(
            "⚠️ Укажи реальный рост в сантиметрах.\n\n"
            "Например: 180"
        )

        return

    await delete_last_bot_message(message, state)

    try:
        await message.delete()
    except Exception:
        pass

    await state.update_data(
        height=height
    )

    question = await message.answer(
        "⚖️ <b>Вес</b>\n\n"
        "Укажи свой текущий вес в килограммах:\n"
        "<i>Например: 75 или 75.5</i>",
        parse_mode="HTML"
    )

    await state.update_data(
        last_bot_message_id=question.message_id
    )

    await state.set_state(
        FoodKbjuForm.weight
    )


# ==========================================
#             ОБРАБОТКА ВЕСА
# ==========================================

@router.message(FoodKbjuForm.weight)
async def process_food_weight(
    message: Message,
    state: FSMContext
):

    try:
        weight = float(
            message.text.replace(",", ".")
        )
    except ValueError:

        await message.answer(
            "⚠️ Введи вес числом.\n\n"
            "Например: 75 или 75.5"
        )

        return

    if weight < 30 or weight > 300:

        await message.answer(
            "⚠️ Укажи реальный вес в килограммах.\n\n"
            "Например: 75 или 75.5"
        )

        return

    await delete_last_bot_message(message, state)

    try:
        await message.delete()
    except Exception:
        pass

    await state.update_data(
        weight=weight
    )

    question = await message.answer(
        "🎯 <b>Цель</b>\n\n"
        "Какая цель сейчас основная?\n"
        "Gym AI подстроит калории и БЖУ под выбранную цель",
        reply_markup=goal_keyboard(),
        parse_mode="HTML"
    )

    await state.update_data(
        last_bot_message_id=question.message_id
    )

    await state.set_state(
        FoodKbjuForm.goal
    )


# ==========================================
#             ОБРАБОТКА ЦЕЛИ
# ==========================================

@router.callback_query(
    FoodKbjuForm.goal,
    F.data.startswith("food_goal_")
)
async def process_food_goal(
    callback: CallbackQuery,
    state: FSMContext
):

    try:
        await callback.message.delete()
    except Exception:
        pass

    goal = callback.data.replace("food_goal_", "")

    await state.update_data(
        goal=goal
    )

    question = await callback.message.answer(
        "🚶 <b>Активность</b>\n\n"
        "Какой у тебя обычный уровень активности вне зала?\n\n"
        "Учитывай работу, шаги, бытовую активность и движение в течение дня",
        reply_markup=activity_keyboard(),
        parse_mode="HTML"
    )

    await state.update_data(
        last_bot_message_id=question.message_id
    )

    await state.set_state(
        FoodKbjuForm.activity
    )

    await callback.answer()


# ==========================================
#          ОБРАБОТКА АКТИВНОСТИ
# ==========================================

@router.callback_query(
    FoodKbjuForm.activity,
    F.data.startswith("food_activity_")
)
async def process_food_activity(
    callback: CallbackQuery,
    state: FSMContext
):

    try:
        await callback.message.delete()
    except Exception:
        pass

    activity = callback.data.replace("food_activity_", "")

    await state.update_data(
        activity=activity
    )

    question = await callback.message.answer(
        "⚡ <b>Темп изменения формы</b>\n\n"
        "Какой темп тебе ближе?\n"
        "Чем быстрее темп, тем жёстче будет корректировка калорий",
        reply_markup=speed_keyboard(),
        parse_mode="HTML"
    )

    await state.update_data(
        last_bot_message_id=question.message_id
    )

    await state.set_state(
        FoodKbjuForm.speed
    )

    await callback.answer()


# ==========================================
#             ОБРАБОТКА ТЕМПА
# ==========================================

@router.callback_query(
    FoodKbjuForm.speed,
    F.data.startswith("food_speed_")
)
async def process_food_speed(
    callback: CallbackQuery,
    state: FSMContext
):

    try:
        await callback.message.delete()
    except Exception:
        pass

    speed = callback.data.replace("food_speed_", "")

    await state.update_data(
        speed=speed
    )

    data = await state.get_data()

    kbju = calculate_kbju(
        age=data["age"],
        gender=data["gender"],
        height=data["height"],
        weight=data["weight"],
        goal=data["goal"],
        activity=data["activity"],
        speed=data["speed"],
    )

    save_user_kbju(
        callback.from_user.id,
        kbju
    )

    await callback.message.answer(
        "✅ <b>КБЖУ рассчитано</b>\n\n"

        "🔥 <b>Твоя дневная норма</b>\n\n"

        f"Калории: <b>{kbju['calories']} ккал</b>\n"
        f"🥩 Белки: <b>{kbju['protein']} г</b>\n"
        f"🧈 Жиры: <b>{kbju['fat']} г</b>\n"
        f"🍚 Углеводы: <b>{kbju['carbs']} г</b>\n\n"

        "━━━━━━━━━━━━━━\n\n"

        "📊 <b>Расчетная база</b>\n"
        f"Базовый обмен: <b>{kbju.get('bmr', '—')} ккал</b>\n"
        f"Поддержание веса: <b>{kbju.get('maintenance', '—')} ккал</b>\n\n"

        "💡 <b>Важно</b>\n"
        "Это расчетная норма. Следи за весом и самочувствием 7–14 дней, "
        "после чего норму можно скорректировать.",
        reply_markup=kbju_result_keyboard(),
        parse_mode="HTML"
    )

    await state.clear()

    await callback.answer()


# ==========================================
#        СТАРТ МЕНЮ ПИТАНИЯ НА ДЕНЬ
# ==========================================

@router.callback_query(F.data == "food_daily_menu")
async def start_daily_menu(callback: CallbackQuery, state: FSMContext):

    # УДАЛЯЕМ ПРЕДЫДУЩЕЕ СООБЩЕНИЕ
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
            "💎 <b>Меню на день доступно в Premium</b>\n\n"
            "Premium составит рацион под твои КБЖУ, продукты "
            "и количество приемов пищи.\n\n"
            "Ты получишь готовый план питания на день "
            "с калориями, белками, жирами и углеводами.",
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
                            text="⬅️ Назад в питание",
                            callback_data="menu_food"
                        )
                    ],
                ]
            ),
            parse_mode="HTML"
        )

        await callback.answer()
        return

    # ==========================================
    #       ПОЛУЧАЕМ КБЖУ ИЗ users.json
    # ==========================================

    kbju = get_user_kbju(
        callback.from_user.id
    )

    # ==========================================
    #       ЕСЛИ КБЖУ НЕТ
    # ==========================================

    if not kbju:

        await callback.message.answer(
            "🍱 <b>Меню на день</b>\n\n"
            "Чтобы составить рацион, сначала нужно рассчитать КБЖУ.\n\n"
            "Нажми кнопку ниже, чтобы перейти к расчету 👇",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🥗 Рассчитать КБЖУ",
                            callback_data="food_calculate_kbju"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="⬅️ Назад в питание",
                            callback_data="menu_food"
                        )
                    ],
                ]
            ),
            parse_mode="HTML"
        )

        await callback.answer()
        return

    # ==========================================
    #       СОХРАНЯЕМ КБЖУ В FSM
    # ==========================================

    await state.update_data(
        kbju=kbju
    )

    question = await callback.message.answer(
        "🍱 <b>Меню питания на день</b>\n\n"
        "🥦 Сейчас я составлю рацион под твои предпочтения.\n\n"
        "Какие продукты можно использовать?\n\n"
        "<i>Например: курица, рис, яйца, творог, овощи, любые</i>",
        parse_mode="HTML"
    )

    await state.update_data(
        last_bot_message_id=question.message_id
    )

    await state.set_state(
        DailyMenuForm.allowed_products
    )

    await callback.answer()


# ==========================================
#       ОБРАБОТКА РАЗРЕШЕННЫХ ПРОДУКТОВ
# ==========================================

@router.message(DailyMenuForm.allowed_products)
async def process_allowed_products(message: Message, state: FSMContext):

    await delete_last_bot_message(message, state)
    await message.delete()

    await state.update_data(
        allowed_products=message.text
    )

    question = await message.answer(
        "🚫 <b>Какие продукты нельзя использовать?</b>\n\n"
        "Напиши продукты, которые ты не ешь или не хочешь видеть в рационе. <i>Например: молоко, свинина, рыба, сахар</i>\n\n"
        "Если ограничений нет — напиши: <b>нет</b>",
        parse_mode="HTML"
    )

    await state.update_data(
        last_bot_message_id=question.message_id
    )

    await state.set_state(
        DailyMenuForm.forbidden_products
    )


# ==========================================
#       ОБРАБОТКА ЗАПРЕЩЕННЫХ ПРОДУКТОВ
# ==========================================

@router.message(DailyMenuForm.forbidden_products)
async def process_forbidden_products(message: Message, state: FSMContext):

    await delete_last_bot_message(message, state)
    await message.delete()

    await state.update_data(
        forbidden_products=message.text
    )

    question = await message.answer(
        "🍽 <b>Сколько приемов пищи сделать за день?</b>\n\n"
        "Напиши число. <i>Например: 3, 4 или 5</i>",
        parse_mode="HTML"
    )

    await state.update_data(
        last_bot_message_id=question.message_id
    )

    await state.set_state(
        DailyMenuForm.meals_count
    )


# ==========================================
#       ГЕНЕРАЦИЯ МЕНЮ НА ДЕНЬ
# ==========================================

@router.message(DailyMenuForm.meals_count)
async def generate_daily_menu(
    message: Message,
    state: FSMContext
):

    # ==========================================
    #       ПРОВЕРКА КОЛИЧЕСТВА ПРИЕМОВ
    # ==========================================

    if not message.text.isdigit():

        await message.answer(
            "Введи количество приемов пищи числом.\n\n"
            "Например: 4"
        )

        return

    # ==========================================
    #       УДАЛЯЕМ ПРОШЛЫЙ ВОПРОС
    # ==========================================

    await delete_last_bot_message(
        message,
        state
    )

    # ==========================================
    #       УДАЛЯЕМ ОТВЕТ ПОЛЬЗОВАТЕЛЯ
    # ==========================================

    await message.delete()

    # ==========================================
    #       СОХРАНЯЕМ КОЛИЧЕСТВО ПРИЕМОВ
    # ==========================================

    await state.update_data(
        meals_count=message.text
    )

    # ==========================================
    #       ПОЛУЧАЕМ ВСЕ ДАННЫЕ
    # ==========================================

    data = await state.get_data()

    # ==========================================
    #       СООБЩЕНИЕ ЗАГРУЗКИ
    # ==========================================

    loading_message = await message.answer(
        "🤖 <b>Gym AI составляет меню...</b>\n\n"
        "Подбираю рацион максимально близко к твоему КБЖУ 🍱",
        parse_mode="HTML"
    )

    # ==========================================
    #       ЗАПРОС В OPENAI
    # ==========================================
    
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=(
            "Ты профессиональный фитнес-нутрициолог "
            "в premium Telegram-приложении Gym AI.\n\n"

            "ТВОЯ ЗАДАЧА:\n"
            "Составить максимально реалистичный рацион питания на день.\n"
            "Рацион должен быть практичным, вкусным, понятным и подходить "
            "для обычного человека.\n\n"

            "ТОЧНОСТЬ:\n"
            "Рацион должен максимально попадать в КБЖУ пользователя.\n"
            "Допустимое отклонение:\n"
            "- калории: не более 5%\n"
            "- белки/жиры/углеводы: не более 10%\n\n"

            "ВАЖНЫЕ ПРАВИЛА:\n"
            "- не придумывай странные блюда\n"
            "- используй обычные продукты\n"
            "- блюда должны сочетаться между собой\n"
            "- рацион должен выглядеть как реальный фитнес-рацион\n"
            "- НЕ используй запрещенные продукты\n"
            "- НЕ повторяй одинаковые блюда много раз\n"
            "- НЕ используй слишком сложные рецепты\n"
            "- указывай реалистичный вес продуктов\n"
            "- если пользователь указал 5 приемов пищи, обязательно используй: "
            "ЗАВТРАК, ВТОРОЙ ЗАВТРАК, ОБЕД, ПОЛДНИК, УЖИН\n"
            "- если пользователь указал другое количество приемов пищи, "
            "адаптируй структуру под это количество\n\n"

            "СТИЛЬ ОФОРМЛЕНИЯ:\n"
            "- красивое оформление для Telegram\n"
            "- используй HTML: <b>текст</b> и <i>текст</i>\n"
            "- НЕ используй Markdown\n"
            "- НЕ используй таблицы\n"
            "- НЕ используй горизонтальные прочерки между приемами пищи\n"
            "- заголовки приемов пищи пиши ЖИРНЫМ КАПСОМ\n"
            "- ЗАВТРАК, ВТОРОЙ ЗАВТРАК, ОБЕД, ПОЛДНИК, УЖИН — всегда жирным капсом\n"
            "- само название блюда пиши обычным текстом\n"
            "- ингредиенты блюда пиши курсивом через <i>...</i>\n"
            "- КБЖУ каждого приема пищи оформляй аккуратно\n\n"

            "ВХОДНЫЕ ДАННЫЕ:\n"
            f"Разрешенные продукты: {data['allowed_products']}\n"
            f"Запрещенные продукты: {data['forbidden_products']}\n"
            f"Количество приемов пищи: {data['meals_count']}\n\n"

            "КБЖУ ПОЛЬЗОВАТЕЛЯ:\n"
            f"🔥 Калории: {data['kbju']['calories']} ккал\n"
            f"🥩 Белки: {data['kbju']['protein']} г\n"
            f"🧈 Жиры: {data['kbju']['fat']} г\n"
            f"🍚 Углеводы: {data['kbju']['carbs']} г\n\n"

            "ФОРМАТ ОТВЕТА СТРОГО ТАКОЙ:\n\n"

            "🍱 <b>МЕНЮ ПИТАНИЯ НА ДЕНЬ</b>\n\n"

            "🎯 <b>ЦЕЛЬ ПО КБЖУ</b>\n"
            f"🔥 {data['kbju']['calories']} ккал\n"
            f"🥩 {data['kbju']['protein']} г белка\n"
            f"🧈 {data['kbju']['fat']} г жиров\n"
            f"🍚 {data['kbju']['carbs']} г углеводов\n\n"

            "🍳 <b>ЗАВТРАК</b>\n"
            "Название блюда обычным текстом\n"
            "<i>"
            "• ингредиент — вес\n"
            "• ингредиент — вес\n"
            "• ингредиент — вес\n"
            "</i>\n"
            "🔥 ... ккал | 🥩 ... г | 🧈 ... г | 🍚 ... г\n\n"

            "🥪 <b>ВТОРОЙ ЗАВТРАК</b>\n"
            "Название блюда обычным текстом\n"
            "<i>"
            "• ингредиент — вес\n"
            "• ингредиент — вес\n"
            "</i>\n"
            "🔥 ... ккал | 🥩 ... г | 🧈 ... г | 🍚 ... г\n\n"

            "🥘 <b>ОБЕД</b>\n"
            "Название блюда обычным текстом\n"
            "<i>"
            "• ингредиент — вес\n"
            "• ингредиент — вес\n"
            "• ингредиент — вес\n"
            "</i>\n"
            "🔥 ... ккал | 🥩 ... г | 🧈 ... г | 🍚 ... г\n\n"

            "🍎 <b>ПОЛДНИК</b>\n"
            "Название блюда обычным текстом\n"
            "<i>"
            "• ингредиент — вес\n"
            "• ингредиент — вес\n"
            "</i>\n"
            "🔥 ... ккал | 🥩 ... г | 🧈 ... г | 🍚 ... г\n\n"

            "🌙 <b>УЖИН</b>\n"
            "Название блюда обычным текстом\n"
            "<i>"
            "• ингредиент — вес\n"
            "• ингредиент — вес\n"
            "• ингредиент — вес\n"
            "</i>\n"
            "🔥 ... ккал | 🥩 ... г | 🧈 ... г | 🍚 ... г\n\n"

            "✅ <b>ИТОГ ЗА ДЕНЬ</b>\n"
            "🔥 Калории: ... ккал\n"
            "🥩 Белки: ... г\n"
            "🧈 Жиры: ... г\n"
            "🍚 Углеводы: ... г\n\n"

            "📊 <b>ОТКЛОНЕНИЕ ОТ ЦЕЛИ</b>\n"
            "🔥 Калории: ...%\n"
            "🥩 Белки: ...%\n"
            "🧈 Жиры: ...%\n"
            "🍚 Углеводы: ...%\n\n"

            "💡 Рацион можно корректировать под аппетит и самочувствие."
        )
    )

    # ==========================================
    #       УДАЛЯЕМ СООБЩЕНИЕ ЗАГРУЗКИ
    # ==========================================

    await loading_message.delete()

    # ==========================================
    #       ОТПРАВЛЯЕМ ГОТОВЫЙ РАЦИОН
    # ==========================================
    

    await message.answer(
    response.output_text,
    reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data="back_to_main_menu"
                )
            ]
        ]
    ),
    parse_mode="HTML"
    )

    # ==========================================
    #       ОЧИЩАЕМ FSM
    # ==========================================

    await state.clear()
    
# ==========================================
#        КЛАВИАТУРА ПРИЕМА ПИЩИ
# ==========================================

def meal_type_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🌅 Завтрак",
                    callback_data="meal_type_breakfast"
                )
            ],
            [
                InlineKeyboardButton(
                    text="☀️ Обед",
                    callback_data="meal_type_lunch"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🌙 Ужин",
                    callback_data="meal_type_dinner"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🍎 Перекус",
                    callback_data="meal_type_snack"
                )
            ],
        ]
    )

# ==========================================
#           СТАРТ ЗАПИСИ БЛЮДА
# ==========================================

@router.callback_query(F.data == "food_add_meal")
async def start_add_meal(
    callback: CallbackQuery,
    state: FSMContext
):

    try:
        await callback.message.delete()
    except Exception:
        pass

    question = await callback.message.answer(
        "✍️ <b>Записать блюдо</b>\n\n"
        "Выбери прием пищи:",
        reply_markup=meal_type_keyboard(),
        parse_mode="HTML"
    )

    await state.update_data(
        last_bot_message_id=question.message_id
    )

    await state.set_state(
        AddMealForm.meal_type
    )

    await callback.answer()

# ==========================================
#        ОБРАБОТКА ПРИЕМА ПИЩИ
# ==========================================

@router.callback_query(
    AddMealForm.meal_type,
    F.data.startswith("meal_type_")
)
async def process_meal_type(
    callback: CallbackQuery,
    state: FSMContext
):

    await callback.message.delete()

    meal_type = callback.data.replace("meal_type_", "")

    await state.update_data(
        meal_type=meal_type
    )

    question = await callback.message.answer(
    "🍽 <b>Добавление блюда</b>\n\n"

    "Опиши максимально подробно, что ты съел.\n\n"

    "📌 Для точного расчета укажи:\n"
    "• название продуктов\n"
    "• примерный вес в граммах\n"
    "• способ приготовления\n"
    "• соусы, масло и добавки\n\n"

    "✅ Примеры:\n\n"

    "• Куриная грудка 200 г и рис 150 г\n"
    "• Омлет из 3 яиц с сыром 30 г\n"
    "• Творог 5% 180 г и банан 120 г\n"
    "• Цезарь с курицей 300 г и соусом\n"
    "• Бургер и картофель фри из Вкусно и точка\n\n"

    "💡 Чем подробнее описание, тем точнее расчет КБЖУ.",
    parse_mode="HTML"
    )

    await state.update_data(
        last_bot_message_id=question.message_id
    )

    await state.set_state(
        AddMealForm.meal_text
    )

    await callback.answer()

# ==========================================
#        ДОСТАЕМ КБЖУ ИЗ ТЕКСТА БЛЮДА
# ==========================================

def parse_meal_kbju(text):

    calories = re.search(r"Калории:\s*.*?(\d+)", text)
    protein = re.search(r"Белки:\s*.*?(\d+)", text)
    fat = re.search(r"Жиры:\s*.*?(\d+)", text)
    carbs = re.search(r"Углеводы:\s*.*?(\d+)", text)

    return {
        "calories": int(calories.group(1)) if calories else 0,
        "protein": int(protein.group(1)) if protein else 0,
        "fat": int(fat.group(1)) if fat else 0,
        "carbs": int(carbs.group(1)) if carbs else 0,
    } 

# ==========================================
#          ОБРАБОТКА ЗАПИСИ БЛЮДА
# ==========================================

@router.message(AddMealForm.meal_text)
async def process_add_meal(
    message: Message,
    state: FSMContext
):

    # ПРОВЕРКА ТЕКСТА
    if len(message.text.strip()) < 3:

        await message.answer(
            "Опиши блюдо чуть подробнее.\n\n"
            "Например: омлет из 3 яиц, хлеб 50 г"
        )

        return

    # УДАЛЯЕМ ВОПРОС БОТА
    await delete_last_bot_message(
        message,
        state
    )

    # СОХРАНЯЕМ ТЕКСТ БЛЮДА
    meal_text = message.text

    # УДАЛЯЕМ СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ
    try:
        await message.delete()
    except Exception:
        pass

    # СООБЩЕНИЕ ЗАГРУЗКИ
    loading_message = await message.answer(
        "🤖 <b>Считаю КБЖУ блюда...</b>\n\n"
        "Анализирую состав и примерные порции 🍽",
        parse_mode="HTML"
    )

    # ЗАПРОС В OPENAI
    try:

        response = client.responses.create(
            model="gpt-4.1-mini",
            input=(
    "Ты профессиональный фитнес-нутрициолог Gym AI.\n"
    "Твоя задача — максимально точно оценить КБЖУ блюда по описанию пользователя.\n\n"

    "ВАЖНО:\n"
    "- если пользователь указал вес продукта в граммах — обязательно учитывай этот вес\n"
    "- если вес не указан — оцени стандартную порцию реалистично\n"
    "- не завышай и не занижай калории без причины\n"
    "- учитывай способ приготовления: жарка, варка, запекание, масло, соусы\n"
    "- если указано масло, соус, сыр, сахар, орехи — обязательно учитывай их калорийность\n"
    "- если блюдо домашнее — оцени как обычную домашнюю порцию\n"
    "- если продукт готовый/магазинный — используй средние значения для такого продукта\n"
    "- если данных мало — сделай аккуратную оценку и напиши, что расчет примерный\n\n"

    "ПРАВИЛА РАСЧЕТА:\n"
    "- белки, жиры и углеводы указывай в граммах\n"
    "- калории указывай в ккал\n"
    "- значения должны быть реалистичными\n"
    "- округляй до целых чисел\n"
    "- итоговые калории должны логично соответствовать БЖУ\n"
    "- не добавляй лишние поля\n\n"

    "БЛЮДО ПОЛЬЗОВАТЕЛЯ:\n"
    f"{meal_text}\n\n"

    "ФОРМАТ ОТВЕТА СТРОГО ТАКОЙ:\n\n"

    "🍽 <b>Название блюда</b>\n"
    "Краткое описание и что было учтено при расчете.\n\n"

    "🔥 Калории: ... ккал\n"
    "🥩 Белки: ... г\n"
    "🧈 Жиры: ... г\n"
    "🍚 Углеводы: ... г\n\n"

    "💡 Краткий комментарий.\n\n"

    "Не используй Markdown.\n"
    "Используй HTML-теги <b> только для названия блюда."
)
        )

    except Exception as e:

        print("OPENAI ERROR:", e)

        try:
            await loading_message.delete()
        except Exception:
            pass

        await message.answer(
            "⚠️ Не получилось рассчитать блюдо.\n\n"
            "Попробуй ещё раз через пару секунд.",
            reply_markup=food_diary_keyboard(),
            parse_mode="HTML"
        )

        return

    # УДАЛЯЕМ СООБЩЕНИЕ ЗАГРУЗКИ
    try:
        await loading_message.delete()
    except Exception:
        pass

    # СОБИРАЕМ КБЖУ БЛЮДА
    data = await state.get_data()
    meal_type = data.get("meal_type", "snack")

    meal_kbju = parse_meal_kbju(
        response.output_text
    )

    # СОХРАНЯЕМ БЛЮДО В ДНЕВНИК
    add_food_diary_entry(
        message.from_user.id,
        {
            "date": str(date.today()),
            "meal_type": meal_type,
            "text": response.output_text,
            "calories": meal_kbju["calories"],
            "protein": meal_kbju["protein"],
            "fat": meal_kbju["fat"],
            "carbs": meal_kbju["carbs"],
        }
    )

    # ОТПРАВЛЯЕМ РЕЗУЛЬТАТ
    await message.answer(
        response.output_text,

        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="➕ Добавить ещё блюдо",
                        callback_data="food_add_meal"
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


# ==========================================
#          НАЗАД К ЗАПИСИ БЛЮДА
# ==========================================

@router.callback_query(F.data == "meal_back")
async def meal_back_handler(
    callback: CallbackQuery,
    state: FSMContext
):

    # ПОЛУЧАЕМ ДАННЫЕ
    data = await state.get_data()

    last_meal = data.get("last_meal")

    # СОХРАНЯЕМ БЛЮДО
    if last_meal:

        add_food_diary_entry(
            callback.from_user.id,
            last_meal
        )

    # УДАЛЯЕМ ТЕКУЩЕЕ СООБЩЕНИЕ
    try:
        await callback.message.delete()
    except Exception:
        pass

    # ВОЗВРАЩАЕМ К ЗАПИСИ
    await callback.message.answer(
        "✍️ <b>Записать блюдо</b>\n\n"
        "Напиши блюдо еще раз или измени описание.\n\n"
        "<i>Например:\n"
        "Курица 200 г, рис 150 г, овощи 100 г</i>",
        parse_mode="HTML"
    )

    await callback.answer()


# ==========================================
#          ОТМЕНА ЗАПИСИ БЛЮДА
# ==========================================

@router.callback_query(F.data == "meal_cancel")
async def meal_cancel_handler(
    callback: CallbackQuery,
    state: FSMContext
):

    # УДАЛЯЕМ ТЕКУЩЕЕ СООБЩЕНИЕ
    try:
        await callback.message.delete()
    except Exception:
        pass

    # ПОЛУЧАЕМ FSM ДАННЫЕ
    data = await state.get_data()

    # ID СООБЩЕНИЯ "ЗАПИСАТЬ БЛЮДО"
    last_bot_message_id = data.get("last_bot_message_id")

    # УДАЛЯЕМ СООБЩЕНИЕ "ЗАПИСАТЬ БЛЮДО"
    if last_bot_message_id:

        try:
            await callback.bot.delete_message(
                chat_id=callback.message.chat.id,
                message_id=last_bot_message_id
            )
        except Exception:
            pass

    # ОЧИЩАЕМ FSM
    await state.clear()

    # ОТПРАВЛЯЕМ МЕНЮ
    await callback.message.answer(
        "❌ Запись блюда отменена.",
        reply_markup=food_diary_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


# ==========================================
#      КЛАВИАТУРА ДНЕВНИКА ПИТАНИЯ
# ==========================================

def food_diary_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="➕ Добавить блюдо",
                    callback_data="food_add_meal"
                )
            ],

            [
                InlineKeyboardButton(
                    text="💧 Добавить воду",
                    callback_data="add_water"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📅 История питания",
                    callback_data="food_history"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🗑 Удалить блюдо",
                    callback_data="delete_meal"
                )
            ],

            [
                InlineKeyboardButton(
                    text="➖ Убрать воду",
                    callback_data="remove_water"
                )
            ],

            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="menu_food"
                )
            ],
        ]
    )

# ==========================================
#              ПРОГРЕСС-БАР
# ==========================================

def progress_bar(current, target):

    if not target or target <= 0:
        return "░" * 10 + " 0%"

    percent = int((current / target) * 100)

    if percent > 100:
        percent = 100

    filled = int(percent / 10)
    empty = 10 - filled

    return "█" * filled + "░" * empty + f" {percent}%"

# ==========================================
#        КЛАВИАТУРА ИСТОРИИ ДНЕВНИКА
# ==========================================

def food_history_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📅 Сегодня",
                    callback_data="diary_today"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📅 Вчера",
                    callback_data="diary_yesterday"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="menu_food"
                )
            ],
        ]
    )

# ==========================================
#       ПОКАЗ ДНЕВНИКА ПО ДАТЕ
# ==========================================

async def show_diary_by_date(callback: CallbackQuery, diary_date: str):

    try:
        await callback.message.delete()
    except Exception:
        pass

    diary = get_food_diary(callback.from_user.id)
    kbju = get_user_kbju(callback.from_user.id)

    water_ml = get_water_amount(
        callback.from_user.id,
        diary_date
    )

    diary_day = [
        meal for meal in diary
        if meal.get("date") == diary_date
    ]

    total_calories = sum(meal.get("calories", 0) for meal in diary_day)
    total_protein = sum(meal.get("protein", 0) for meal in diary_day)
    total_fat = sum(meal.get("fat", 0) for meal in diary_day)
    total_carbs = sum(meal.get("carbs", 0) for meal in diary_day)

    diary_text = (
        "📔 <b>Дневник питания</b>\n\n"
        f"📅 Дата: <b>{diary_date}</b>\n\n"
    )

    if kbju:

        diary_text += (
            "📊 <b>СТАТИСТИКА ДНЯ</b>\n\n"

            f"🔥 Калории: <b>{total_calories} / {kbju['calories']} ккал</b>\n"
            f"{progress_bar(total_calories, kbju['calories'])}\n\n"

            f"🥩 Белки: <b>{total_protein} / {kbju['protein']} г</b>\n"
            f"{progress_bar(total_protein, kbju['protein'])}\n\n"

            f"🧈 Жиры: <b>{total_fat} / {kbju['fat']} г</b>\n"
            f"{progress_bar(total_fat, kbju['fat'])}\n\n"

            f"🍚 Углеводы: <b>{total_carbs} / {kbju['carbs']} г</b>\n"
            f"{progress_bar(total_carbs, kbju['carbs'])}\n\n"
        )

    else:

        diary_text += (
            "📊 <b>ИТОГ ЗА ДЕНЬ</b>\n"
            f"🔥 Калории: <b>{total_calories} ккал</b>\n"
            f"🥩 Белки: <b>{total_protein} г</b>\n"
            f"🧈 Жиры: <b>{total_fat} г</b>\n"
            f"🍚 Углеводы: <b>{total_carbs} г</b>\n\n"
        )

    diary_text += (
        "💧 <b>ВОДА</b>\n"
        f"Выпито: <b>{water_ml / 1000:.1f} л</b>\n\n"
    )

    if not diary_day:

        diary_text += "За этот день пока нет записанных блюд."

    else:

        meal_type_map = {
            "breakfast": "🌅 <b>ЗАВТРАК</b>",
            "lunch": "☀️ <b>ОБЕД</b>",
            "dinner": "🌙 <b>УЖИН</b>",
            "snack": "🍎 <b>ПЕРЕКУС</b>",
        }

        for index, meal in enumerate(diary_day, start=1):

            meal_type = meal.get("meal_type", "snack")

            diary_text += (
                f"\n{meal_type_map.get(meal_type, '🍽 <b>ПРИЕМ ПИЩИ</b>')}\n"
                f"{meal['text']}\n"
            )

    await callback.message.answer(
        diary_text,
        reply_markup=food_diary_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()

# ==========================================
#             ДНЕВНИК ПИТАНИЯ
# ==========================================

@router.callback_query(F.data == "food_diary")
async def food_diary_handler(callback: CallbackQuery):

    try:
        await callback.message.delete()
    except Exception:
        pass

    is_premium = get_premium_status(
        callback.from_user.id
    )

    if not is_premium:

        await callback.message.answer(
            "💎 <b>Дневник питания доступен в Premium</b>\n\n"
            "Premium откроет:\n"
            "• запись блюд\n"
            "• учет воды\n"
            "• дневник питания по дням\n"
            "• подсчет съеденных КБЖУ\n"
            "• историю питания\n\n"
            "Чтобы вести питание каждый день — активируй Premium.",
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
                            text="⬅️ Назад в питание",
                            callback_data="menu_food"
                        )
                    ],
                ]
            ),
            parse_mode="HTML"
        )

        await callback.answer()
        return

    await show_diary_by_date(
        callback,
        str(date.today())
    )


# ==========================================
#      КЛАВИАТУРА УДАЛЕНИЯ БЛЮДА
# ==========================================

def delete_meal_keyboard(diary):

    meal_type_map = {
        "breakfast": "🌅 Завтрак",
        "lunch": "☀️ Обед",
        "dinner": "🌙 Ужин",
        "snack": "🍎 Перекус",
    }

    buttons = []

    for index, meal in enumerate(diary, start=1):

        meal_type = meal.get("meal_type", "snack")
        meal_name = meal_type_map.get(meal_type, "🍽 Блюдо")

        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"🗑 {index}. {meal_name}",
                    callback_data=f"delete_meal_{index - 1}"
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="food_diary"
            )
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


# ==========================================
#          УДАЛЕНИЕ БЛЮДА
# ==========================================

@router.callback_query(F.data == "delete_meal")
async def delete_meal_handler(callback: CallbackQuery):

    try:
        await callback.message.delete()
    except Exception:
        pass

    diary = get_food_diary(
        callback.from_user.id
    )

    today = str(date.today())

    diary_today = [
        meal for meal in diary
        if meal.get("date") == today
    ]

    if not diary_today:

        await callback.message.answer(
            "❌ <b>Удаление блюда</b>\n\n"
            "Сегодня пока нет записанных блюд.",
            reply_markup=food_diary_keyboard(),
            parse_mode="HTML"
        )

        await callback.answer()
        return

    await callback.message.answer(
        "🗑 <b>Удаление блюда</b>\n\n"
        "Выбери блюдо, которое нужно удалить:",
        reply_markup=delete_meal_keyboard(diary_today),
        parse_mode="HTML"
    )

    await callback.answer()


# ==========================================
#       УДАЛЕНИЕ БЛЮДА ПО КНОПКЕ
# ==========================================

@router.callback_query(F.data.startswith("delete_meal_"))
async def delete_meal_by_button(callback: CallbackQuery):

    index = int(
        callback.data.replace("delete_meal_", "")
    )

    success = delete_food_diary_entry(
        callback.from_user.id,
        index
    )

    try:
        await callback.message.delete()
    except Exception:
        pass

    if success:

        await callback.answer(
        "Блюдо удалено"
        )

        await food_diary_handler(callback)

    else:

        await callback.message.answer(
        "❌ Не удалось удалить блюдо.",
        reply_markup=food_diary_keyboard(),
        parse_mode="HTML"
        )

        await callback.answer()


## ==========================================
#        ОБРАБОТКА НОМЕРА ДЛЯ УДАЛЕНИЯ
# ==========================================

@router.message(AddMealForm.delete_meal)
async def process_delete_meal(
    message: Message,
    state: FSMContext
):

    # УДАЛЯЕМ СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ С НОМЕРОМ
    try:
        await message.delete()
    except Exception:
        pass

    # ПРОВЕРКА НОМЕРА
    if not message.text.isdigit():

        await message.answer(
            "❌ Введи номер блюда цифрой."
        )

        return

    meal_index = int(message.text) - 1

    success = delete_food_diary_entry(
        message.from_user.id,
        meal_index
    )

    if not success:

        await message.answer(
            "❌ Блюдо не найдено.",
            reply_markup=food_diary_keyboard(),
            parse_mode="HTML"
        )

        await state.clear()
        return

    await message.answer(
        "✅ Блюдо удалено.",
        reply_markup=food_diary_keyboard(),
        parse_mode="HTML"
    )

    await state.clear()

# ==========================================
#            КЛАВИАТУРА ВОДЫ
# ==========================================

def water_keyboard(action):

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="250 мл",
                    callback_data=f"{action}_250"
                ),

                InlineKeyboardButton(
                    text="500 мл",
                    callback_data=f"{action}_500"
                ),
            ],

            [
                InlineKeyboardButton(
                    text="1 л",
                    callback_data=f"{action}_1000"
                )
            ],

            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="food_diary"
                )
            ],

        ]
    )

# ==========================================
#              ДОБАВИТЬ ВОДУ
# ==========================================

@router.callback_query(F.data == "add_water")
async def add_water_handler(callback: CallbackQuery):

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        "💧 <b>Добавить воду</b>\n\n"
        "Выбери количество:",
        reply_markup=water_keyboard("addwater"),
        parse_mode="HTML"
    )

    await callback.answer()


# ==========================================
#              УБРАТЬ ВОДУ
# ==========================================

@router.callback_query(F.data == "remove_water")
async def remove_water_handler(callback: CallbackQuery):

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        "➖ <b>Убрать воду</b>\n\n"
        "Выбери количество:",
        reply_markup=water_keyboard("removewater"),
        parse_mode="HTML"
    )

    await callback.answer()


# ==========================================
#          ОБРАБОТЧИК ДОБАВЛЕНИЕ ВОДЫ
# ==========================================

@router.callback_query(F.data.startswith("addwater_"))
async def add_water_amount(callback: CallbackQuery):

    amount = int(
        callback.data.replace("addwater_", "")
    )

    add_water_entry(
        callback.from_user.id,
        amount,
        str(date.today())
    )

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.answer(
    f"Добавлено {amount} мл"
)

    await food_diary_handler(callback)


# ==========================================
#           ОБРАБОТЧИК УДАЛЕНИЕ ВОДЫ
# ==========================================

@router.callback_query(F.data.startswith("removewater_"))
async def remove_water_amount(callback: CallbackQuery):

    amount = int(
        callback.data.replace("removewater_", "")
    )

    remove_water_entry(
        callback.from_user.id,
        amount,
        str(date.today())
    )

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.answer(
    f"Убрано {amount} мл"
)

    await food_diary_handler(callback)


# ==========================================
#          ИСТОРИЯ ДНЕВНИКА
# ==========================================

@router.callback_query(F.data == "food_history")
async def food_history_handler(callback: CallbackQuery):

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        "📅 <b>История дневника</b>\n\n"
        "Выбери день:",
        reply_markup=food_history_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


# ==========================================
#       ОБРАБОТЧИК ДНЕВНИКА ЗА СЕГОДНЯ
# ==========================================

@router.callback_query(F.data == "diary_today")
async def diary_today_handler(callback: CallbackQuery):

    await show_diary_by_date(
        callback,
        str(date.today())
    )


# ==========================================
#       ОБРАБОТЧИК ДНЕВНИКа ЗА ВЧЕРА
# ==========================================

@router.callback_query(F.data == "diary_yesterday")
async def diary_yesterday_handler(callback: CallbackQuery):

    yesterday = date.today() - timedelta(days=1)

    await show_diary_by_date(
        callback,
        str(yesterday)
    )


# ==========================================
#          AI АНАЛИЗ ПИТАНИЯ
# ==========================================

@router.callback_query(F.data == "food_ai_analysis")
async def food_ai_analysis_handler(callback: CallbackQuery):

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
            "💎 <b>AI анализ питания доступен в Premium</b>\n\n"
            "Gym AI проанализирует:\n"
            "• калории\n"
            "• белки, жиры и углеводы\n"
            "• воду\n"
            "• качество рациона\n"
            "• соответствие твоей цели\n\n"
            "И даст персональные рекомендации по питанию.",
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
                            text="⬅️ Назад в питание",
                            callback_data="menu_food"
                        )
                    ],
                ]
            ),
            parse_mode="HTML"
        )

        await callback.answer()
        return

    # ==========================================
    #          ПОЛУЧАЕМ ДАННЫЕ
    # ==========================================

    today = str(date.today())

    kbju = get_user_kbju(
        callback.from_user.id
    )

    diary = get_food_diary(
        callback.from_user.id
    )

    today_food = [
        meal for meal in diary
        if meal.get("date") == today
    ]

    water_ml = get_water_amount(
        callback.from_user.id,
        today
    )

    if not kbju:

        await callback.message.answer(
            "🤖 <b>AI анализ питания</b>\n\n"
            "Сначала нужно рассчитать КБЖУ, чтобы Gym AI мог сравнить рацион с твоей нормой.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔥 Рассчитать КБЖУ",
                            callback_data="food_calculate_kbju"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="⬅️ Назад в питание",
                            callback_data="menu_food"
                        )
                    ],
                ]
            ),
            parse_mode="HTML"
        )

        await callback.answer()
        return

    if not today_food:

        await callback.message.answer(
            "🤖 <b>AI анализ питания</b>\n\n"
            "Сегодня в дневнике пока нет блюд.\n\n"
            "Добавь хотя бы один прием пищи, чтобы Gym AI мог проанализировать рацион.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="📔 Открыть дневник",
                            callback_data="food_diary"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="⬅️ Назад в питание",
                            callback_data="menu_food"
                        )
                    ],
                ]
            ),
            parse_mode="HTML"
        )

        await callback.answer()
        return

    loading_message = await callback.message.answer(
        "🤖 <b>Gym AI анализирует питание...</b>\n\n"
        "Смотрю КБЖУ, блюда и воду за сегодня.",
        parse_mode="HTML"
    )

    try:

        response = client.responses.create(
            model="gpt-4.1-mini",
            input=(
                "Ты AI-нутрициолог Gym AI.\n"
                "Проанализируй питание пользователя за сегодня на русском языке.\n"
                "Не ставь диагнозы и не давай медицинских обещаний.\n\n"

                "НОРМА КБЖУ:\n"
                f"Калории: {kbju['calories']} ккал\n"
                f"Белки: {kbju['protein']} г\n"
                f"Жиры: {kbju['fat']} г\n"
                f"Углеводы: {kbju['carbs']} г\n\n"

                "ПИТАНИЕ ЗА СЕГОДНЯ:\n"
                f"{today_food}\n\n"

                "ВОДА ЗА СЕГОДНЯ:\n"
                f"{water_ml} мл\n\n"

                "ФОРМАТ ОТВЕТА:\n\n"
                "🤖 <b>AI анализ питания</b>\n\n"

                "📊 <b>Общая оценка</b>\n"
                "Коротко оцени рацион за сегодня.\n\n"

                "✅ <b>Что хорошо</b>\n"
                "• ...\n"
                "• ...\n\n"

                "⚠️ <b>Что улучшить</b>\n"
                "• ...\n"
                "• ...\n\n"

                "💧 <b>Вода</b>\n"
                "Оцени водный баланс.\n\n"

                "🎯 <b>Рекомендации Gym AI</b>\n"
                "• ...\n"
                "• ...\n"
                "• ...\n\n"

                "Не используй Markdown. Используй только HTML <b>."
            )
        )

    except Exception as e:

        print("FOOD AI ANALYSIS ERROR:", e)

        try:
            await loading_message.delete()
        except Exception:
            pass

        await callback.message.answer(
            "⚠️ <b>AI анализ питания временно недоступен</b>\n\n"
            "Попробуй ещё раз через пару секунд.",
            reply_markup=food_menu_keyboard(True),
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
        reply_markup=food_menu_keyboard(True),
        parse_mode="HTML"
    )

    await callback.answer()