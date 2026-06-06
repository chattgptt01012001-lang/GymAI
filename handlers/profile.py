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
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from keyboards.main_menu import main_menu_keyboard

# ==========================================
#          ИМПОРТ ХРАНИЛИЩА
# ==========================================

from storage import register_user, save_user_profile, save_user_kbju, get_user_kbju

# ==========================================
#            СОЗДАНИЕ ROUTER
# ==========================================

router = Router()


# ==========================================
#            КАНАЛ TELEGRAM
# ==========================================

CHANNEL_USERNAME = "@gymaiofficialchannel"
CHANNEL_URL = "https://t.me/gymaiofficialchannel"


# ==========================================
#         СОСТОЯНИЯ АНКЕТЫ FSM
# ==========================================

class ProfileForm(StatesGroup):

    # ШАГ 1 — ПОЛ
    gender = State()

    # ШАГ 2 — ВОЗРАСТ
    age = State()

    # ШАГ 3 — РОСТ
    height = State()

    # ШАГ 4 — НЫНЕШНИЙ ВЕС
    weight = State()

    # ШАГ 5 — ЦЕЛЬ
    goal = State()

    # ШАГ 6 — АКТИВНОСТЬ
    activity = State()

    # ШАГ 7 — ОПЫТ ТРЕНИРОВОК
    training_experience = State()

    # ШАГ 8 — ТЕМП ИЗМЕНЕНИЯ ТЕЛА
    body_change_speed = State()

    # ШАГ 9 — ОГРАНИЧЕНИЯ / ТРАВМЫ
    limitations = State()

    # ШАГ 10 — ЖЕЛАЕМЫЙ РЕЗУЛЬТАТ
    desired_result = State()


# ==========================================
#        КЛАВИАТУРА ВЫБОРА ПОЛА
# ==========================================

def gender_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Мужчина",
                    callback_data="gender_male"
                ),
                InlineKeyboardButton(
                    text="Женщина",
                    callback_data="gender_female"
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
                    callback_data="goal_loss"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Поддержание формы",
                    callback_data="goal_maintain"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Набор массы",
                    callback_data="goal_gain"
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
                    callback_data="activity_low"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🚶 Легкая активность 1–2 раза в неделю",
                    callback_data="activity_light"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🏃 Средняя активность 3–4 раза в неделю",
                    callback_data="activity_medium"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🏋️ Высокая активность 5–7 раз в неделю",
                    callback_data="activity_high"
                )
            ],

            [
                InlineKeyboardButton(
                    text="💪 Физическая работа + спорт",
                    callback_data="activity_very_high"
                )
            ],
        ]
    )


# ==========================================
#      КЛАВИАТУРА ОПЫТА ТРЕНИРОВОК
# ==========================================

def training_experience_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Новичок",
                    callback_data="experience_beginner"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Средний уровень",
                    callback_data="experience_intermediate"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Опытный",
                    callback_data="experience_advanced"
                )
            ],
        ]
    )


# ==========================================
#      КЛАВИАТУРА ТЕМПА ИЗМЕНЕНИЯ ТЕЛА
# ==========================================

def body_change_speed_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="🐢 Плавно",
                    callback_data="speed_slow"
                )
            ],

            [
                InlineKeyboardButton(
                    text="⚡ Умеренно",
                    callback_data="speed_medium"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🔥 Быстро",
                    callback_data="speed_fast"
                )
            ],

            [
                InlineKeyboardButton(
                    text="☠️ Экстремальная весогонка",
                    callback_data="speed_extreme"
                )
            ],
        ]
    )


# ==========================================
#      КЛАВИАТУРА ОГРАНИЧЕНИЙ / ТРАВМ
# ==========================================

def limitations_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Нет ограничений",
                    callback_data="limitations_no"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Есть ограничения",
                    callback_data="limitations_yes"
                )
            ],
        ]
    )


# ==========================================
#          КЛАВИАТУРА ПОДПИСКИ
# ==========================================

def subscribe_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Перейти в канал",
                    url=CHANNEL_URL
                )
            ],
            [
                InlineKeyboardButton(
                    text="Я подписался",
                    callback_data="check_subscription"
                )
            ],
        ]
    )

def after_profile_summary_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data="back_to_main_menu"
                )
            ]
        ]
    )


# ==========================================
#        УДАЛЕНИЕ ПОСЛЕДНЕГО СООБЩЕНИЯ БОТА
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
    body_change_speed
):

    # ПРЕОБРАЗУЕМ ДАННЫЕ В ЧИСЛА
    age = int(age)
    height = int(height)
    weight = float(weight)

    # РАСЧЕТ БАЗОВОГО ОБМЕНА
    if gender == "male":

        bmr = 10 * weight + 6.25 * height - 5 * age + 5

    else:

        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    # КОЭФФИЦИЕНТЫ АКТИВНОСТИ
    activity_map = {

    # СИЖУ ДОМА
        "low": 1.2,
    # ЛЕГКАЯ АКТИВНОСТЬ
        "light": 1.375,
    # СРЕДНЯЯ АКТИВНОСТЬ
        "medium": 1.55,
    # ВЫСОКАЯ АКТИВНОСТЬ
        "high": 1.725,
    # ФИЗИЧЕСКАЯ РАБОТА + СПОРТ
        "very_high": 1.9,
    }

    calories = bmr * activity_map[activity]

    # КОРРЕКТИРОВКА ПО ТЕМПУ
    speed_map = {

    # ПЛАВНО
        "slow": 200,
    # УМЕРЕННО
       "medium": 400,
    # БЫСТРО
       "fast": 600,
    # ЭКСТРЕМАЛЬНО
       "extreme": 900,
    }

    correction = speed_map[body_change_speed]

    # КОРРЕКТИРОВКА ПОД ЦЕЛЬ
    if goal == "loss":

        calories -= correction

    elif goal == "gain":

        calories += correction

    # РАСЧЕТ БЖУ
    protein = weight * 1.8
    fat = weight * 0.9
    carbs = (calories - protein * 4 - fat * 9) / 4

    return {
        "calories": round(calories),
        "protein": round(protein),
        "fat": round(fat),
        "carbs": round(carbs),
    }


# ==========================================
#              СТАРТ АНКЕТЫ 1 РАЗ
# ==========================================

@router.callback_query(F.data == "start_onboarding")
async def start_onboarding(
    callback: CallbackQuery,
    state: FSMContext
):

    await callback.message.delete()

    question = await callback.message.answer(
        "📋 <b>Шаг 1/11</b> Начнем с самого главного: укажи пол:\n\n"
        "Так расчет КБЖУ будет максимально точным.",
        reply_markup=gender_keyboard(),
        parse_mode="HTML"
    )

    await state.update_data(
        last_bot_message_id=question.message_id
    )

    await state.set_state(
        ProfileForm.gender
    )

    await callback.answer()

# ==========================================
#              СТАРТ АНКЕТЫ 
# ==========================================

@router.callback_query(F.data == "edit_profile")
async def edit_profile(
    callback: CallbackQuery,
    state: FSMContext
):

    await callback.message.delete()

    await state.update_data(
        edit_mode=True
    )

    question = await callback.message.answer(
        "📋 <b>Шаг 1/10</b>\n\n"
        "Начнем с самого главного: укажи пол.\n\n"
        "Так расчет КБЖУ будет максимально точным.",
        reply_markup=gender_keyboard(),
        parse_mode="HTML"
    )

    await state.update_data(
        last_bot_message_id=question.message_id
    )

    await state.set_state(
        ProfileForm.gender
    )

    await callback.answer()

# ==========================================
#             ОБРАБОТКА ПОЛА
# ==========================================

@router.callback_query(
    ProfileForm.gender,
    F.data.startswith("gender_")
)
async def process_gender(
    callback: CallbackQuery,
    state: FSMContext
):

    await callback.message.delete()

    gender = callback.data.replace("gender_", "")

    await state.update_data(
        gender=gender
    )

    question = await callback.message.answer(
        "📋 <b>Шаг 2/11</b> Сколько тебе полных лет? Например: 25",
        parse_mode="HTML"
    )

    await state.update_data(
        last_bot_message_id=question.message_id
    )

    await state.set_state(
        ProfileForm.age
    )

    await callback.answer()


# ==========================================
#          ОБРАБОТКА ВОЗРАСТА
# ==========================================

@router.message(ProfileForm.age)
async def process_age(
    message: Message,
    state: FSMContext
):

    if not message.text.isdigit():

        await message.answer(
            "Введи возраст числом.\n\n"
            "Например: 25"
        )

        return

    await delete_last_bot_message(message, state)
    await message.delete()

    await state.update_data(
        age=message.text
    )

    question = await message.answer(
        "📋 <b>Шаг 3/11</b> Укажи свой рост в сантиметрах? Например: 180",
        parse_mode="HTML"
    )

    await state.update_data(
        last_bot_message_id=question.message_id
    )

    await state.set_state(
        ProfileForm.height
    )


# ==========================================
#            ОБРАБОТКА РОСТА
# ==========================================

@router.message(ProfileForm.height)
async def process_height(
    message: Message,
    state: FSMContext
):

    if not message.text.isdigit():

        await message.answer(
            "Введи рост числом.\n\n"
            "Например: 180"
        )

        return

    await delete_last_bot_message(message, state)
    await message.delete()

    await state.update_data(
        height=message.text
    )

    question = await message.answer(
        "📋 <b>Шаг 4/11</b> Сколько ты сейчас весишь? Например: 75 или 75.5",
        parse_mode="HTML"
    )

    await state.update_data(
        last_bot_message_id=question.message_id
    )

    await state.set_state(
        ProfileForm.weight
    )


# ==========================================
#             ОБРАБОТКА ВЕСА
# ==========================================

@router.message(ProfileForm.weight)
async def process_weight(
    message: Message,
    state: FSMContext
):

    try:

        weight = float(
            message.text.replace(",", ".")
        )

    except ValueError:

        await message.answer(
            "Введи вес числом.\n\n"
            "Например: 75 или 75.5"
        )

        return

    await delete_last_bot_message(message, state)
    await message.delete()

    await state.update_data(
        weight=weight
    )

    question = await message.answer(
        "📋 <b>Шаг 5/11</b> Какая главная цель - похудение, поддержание веса или набор массы?\n\n"
        "Выбери вариант ниже",
        reply_markup=goal_keyboard(),
        parse_mode="HTML"
    )

    await state.update_data(
        last_bot_message_id=question.message_id
    )

    await state.set_state(
        ProfileForm.goal
    )


# ==========================================
#             ОБРАБОТКА ЦЕЛИ
# ==========================================

@router.callback_query(
    ProfileForm.goal,
    F.data.startswith("goal_")
)
async def process_goal(
    callback: CallbackQuery,
    state: FSMContext
):

    await callback.message.delete()

    goal = callback.data.replace("goal_", "")

    await state.update_data(
        goal=goal
    )

    question = await callback.message.answer(
        "📋 <b>Шаг 6/11</b> Какой у тебя уровень активности вне зала — работа, быт, шаги в течение дня?",
        reply_markup=activity_keyboard(),
        parse_mode="HTML"
    )

    await state.update_data(
        last_bot_message_id=question.message_id
    )

    await state.set_state(
        ProfileForm.activity
    )

    await callback.answer()


# ==========================================
#          ОБРАБОТКА АКТИВНОСТИ
# ==========================================

@router.callback_query(
    ProfileForm.activity,
    F.data.startswith("activity_")
)
async def process_activity(
    callback: CallbackQuery,
    state: FSMContext
):

    await callback.message.delete()

    activity = callback.data.replace("activity_", "")

    await state.update_data(
        activity=activity
    )

    question = await callback.message.answer(
        "📋 <b>Шаг 7/11</b> Какой у тебя опыт тренировок?",
        reply_markup=training_experience_keyboard(),
        parse_mode="HTML"
    )

    await state.update_data(
        last_bot_message_id=question.message_id
    )

    await state.set_state(
        ProfileForm.training_experience
    )

    await callback.answer()


# ==========================================
#       ОБРАБОТКА ОПЫТА ТРЕНИРОВОК
# ==========================================

@router.callback_query(
    ProfileForm.training_experience,
    F.data.startswith("experience_")
)
async def process_training_experience(
    callback: CallbackQuery,
    state: FSMContext
):

    await callback.message.delete()

    training_experience = callback.data.replace("experience_", "")

    await state.update_data(
        training_experience=training_experience
    )

    question = await callback.message.answer(
        "📋 <b>Шаг 8/11</b> Выбери темп изменения тела.\n\n"
        "Плавно — мягкий режим.\n"
        "Умеренно — оптимальный баланс.\n"
        "Быстро — более агрессивный темп.\n"
        "Экстремальная весогонка - только для спортсменов",
        reply_markup=body_change_speed_keyboard(),
        parse_mode="HTML"
    )

    await state.update_data(
        last_bot_message_id=question.message_id
    )

    await state.set_state(
        ProfileForm.body_change_speed
    )

    await callback.answer()


# ==========================================
#     ОБРАБОТКА ТЕМПА ИЗМЕНЕНИЯ ТЕЛА
# ==========================================

@router.callback_query(
    ProfileForm.body_change_speed,
    F.data.startswith("speed_")
)
async def process_body_change_speed(
    callback: CallbackQuery,
    state: FSMContext
):

    await callback.message.delete()

    body_change_speed = callback.data.replace("speed_", "")

    await state.update_data(
        body_change_speed=body_change_speed
    )

    question = await callback.message.answer(
        "📋 <b>Шаг 9/11</b> Есть ли у тебя ограничения, травмы или противопоказания?",
        reply_markup=limitations_keyboard(),
        parse_mode="HTML"
    )

    await state.update_data(
        last_bot_message_id=question.message_id
    )

    await state.set_state(
        ProfileForm.limitations
    )

    await callback.answer()


# ==========================================
#       ОБРАБОТКА ОГРАНИЧЕНИЙ / ТРАВМ
# ==========================================

@router.callback_query(
    ProfileForm.limitations,
    F.data.startswith("limitations_")
)
async def process_limitations(
    callback: CallbackQuery,
    state: FSMContext
):

    await callback.message.delete()

    limitations = callback.data.replace("limitations_", "")

    await state.update_data(
        limitations=limitations
    )

    question = await callback.message.answer(
        "📋 <b>Шаг 10/11</b> Опиши желаемый результат.\n\n"
        "Например: хочу похудеть на 5 кг, подтянуть тело и улучшить выносливость.",
        parse_mode="HTML"
    )

    await state.update_data(
        last_bot_message_id=question.message_id
    )

    await state.set_state(
        ProfileForm.desired_result
    )

    await callback.answer()


# ==========================================
#       ОБРАБОТКА ЖЕЛАЕМОГО РЕЗУЛЬТАТА
# ==========================================

@router.message(ProfileForm.desired_result)
async def process_desired_result(
    message: Message,
    state: FSMContext
):

    # ==========================================
    #          ПРОВЕРКА ТЕКСТА
    # ==========================================

    if len(message.text.strip()) < 3:

        await message.answer(
            "Напиши желаемый результат чуть подробнее."
        )

        return

    # ==========================================
    #       УДАЛЯЕМ ВОПРОС БОТА
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
    #       СОХРАНЯЕМ ЖЕЛАЕМЫЙ РЕЗУЛЬТАТ
    # ==========================================

    await state.update_data(
        desired_result=message.text
    )

    # ==========================================
    #       ПОЛУЧАЕМ ВСЕ ДАННЫЕ АНКЕТЫ
    # ==========================================

    data = await state.get_data()

    # ==========================================
    #              РАСЧЕТ КБЖУ
    # ==========================================

    kbju = calculate_kbju(
        age=data["age"],
        gender=data["gender"],
        height=data["height"],
        weight=data["weight"],
        goal=data["goal"],
        activity=data["activity"],
        body_change_speed=data["body_change_speed"],
    )

    # ==========================================
    #          СОХРАНЯЕМ ПРОФИЛЬ
    # ==========================================

    save_user_profile(
        message.from_user.id,
        {
            "gender": data["gender"],
            "age": data["age"],
            "height": data["height"],
            "weight": data["weight"],
            "goal": data["goal"],
            "activity": data["activity"],
            "training_experience": data["training_experience"],
            "body_change_speed": data["body_change_speed"],
            "limitations": data["limitations"],
            "desired_result": data["desired_result"],
        }
    )

    # ==========================================
    #          СОХРАНЯЕМ КБЖУ
    # ==========================================

    save_user_kbju(
        message.from_user.id,
        kbju
    )

    # ==========================================
    #       ЕСЛИ ЭТО РЕДАКТИРОВАНИЕ ПРОФИЛЯ
    # ==========================================

    if data.get("edit_mode"):

        await message.answer(
            "✅ <b>Твой профиль Gym AI обновлен</b>\n\n"

            "Данные сохранены. Новое КБЖУ рассчитано 👇\n\n"

            "📊 <b>КБЖУ</b>\n"
            f"🔥 Калории: <b>{kbju['calories']} ккал</b>\n"
            f"🥩 Белки: <b>{kbju['protein']} г</b>\n"
            f"🧈 Жиры: <b>{kbju['fat']} г</b>\n"
            f"🍚 Углеводы: <b>{kbju['carbs']} г</b>\n\n"

            "Нажми кнопку ниже, чтобы перейти в главное меню.",

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

        await state.clear()
        return

    # ==========================================
    #       ЕСЛИ ЭТО ПЕРВИЧНОЕ ЗАПОЛНЕНИЕ
    # ==========================================

    subscribe_message = await message.answer(
        "📋 <b>Шаг 11/11</b>\n\n"
        "🔒 <b>Чтобы начать полностью пользоваться Gym AI</b>, "
        "нужно подписаться на наш Telegram-канал.\n\n"
        "После подписки тебе откроются:\n"
        "• дневник питания\n"
        "• тренировки\n"
        "• прогресс\n"
        "• персональные рекомендации\n\n"
        "После подписки нажми кнопку ниже.",
        reply_markup=subscribe_keyboard(),
        parse_mode="HTML"
    )

    # ==========================================
    #       СОХРАНЯЕМ ID ЭКРАНА ПОДПИСКИ
    # ==========================================

    await state.update_data(
        last_bot_message_id=subscribe_message.message_id
    )


# ==========================================
#          ПРОВЕРКА ПОДПИСКИ
# ==========================================

@router.callback_query(F.data == "check_subscription")
async def check_subscription(
    callback: CallbackQuery,
    state: FSMContext
):

    # ==========================================
    #          ПРОВЕРЯЕМ ПОДПИСКУ
    # ==========================================

    try:

        member = await callback.bot.get_chat_member(
            chat_id=CHANNEL_USERNAME,
            user_id=callback.from_user.id
        )

    except Exception:

        await callback.answer(
            "Не могу проверить подписку. Проверь, что бот добавлен админом в канал.",
            show_alert=True
        )

        return

    # ==========================================
    #          ЕСЛИ ПОДПИСАН
    # ==========================================

    if member.status in [
        "member",
        "administrator",
        "creator"
    ]:

        # РЕГИСТРИРУЕМ ПОЛЬЗОВАТЕЛЯ
        register_user(
            callback.from_user.id,
            {
                "registered": True
            }
        )

        # ПОЛУЧАЕМ СОХРАНЕННОЕ КБЖУ
        kbju = get_user_kbju(
            callback.from_user.id
        )

        # УДАЛЯЕМ ЭКРАН ПОДПИСКИ
        await callback.message.delete()

        # ЕСЛИ КБЖУ НЕ НАЙДЕНО
        if not kbju:

            await callback.message.answer(
                "✅ <b>Подписка подтверждена</b>\n\n"
                "Но КБЖУ пока не найдено.\n\n"
                "Перейди в главное меню и рассчитай КБЖУ в разделе питания.",

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

            await state.clear()
            await callback.answer()
            return

        # ПОКАЗЫВАЕМ СВОДКУ ПОСЛЕ РЕГИСТРАЦИИ
        await callback.message.answer(
            "✅ <b>Профиль Gym AI готов</b>\n\n"

            "Твои данные сохранены. Теперь Gym AI сможет подбирать питание, "
            "тренировки и рекомендации точнее.\n\n"

            "📊 <b>Твое КБЖУ</b>\n"
            f"🔥 Калории: <b>{kbju['calories']} ккал</b>\n"
            f"🥩 Белки: <b>{kbju['protein']} г</b>\n"
            f"🧈 Жиры: <b>{kbju['fat']} г</b>\n"
            f"🍚 Углеводы: <b>{kbju['carbs']} г</b>\n\n"

            "Нажми кнопку ниже, чтобы перейти в главное меню 👇",

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

        await state.clear()

    # ==========================================
    #          ЕСЛИ НЕ ПОДПИСАН
    # ==========================================

    else:

        await callback.answer(
            "Сначала подпишись на канал.",
            show_alert=True
        )

    await callback.answer()