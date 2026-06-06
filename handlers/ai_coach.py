# ==========================================
#               ИМПОРТЫ
# ==========================================

from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from openai import OpenAI
from config import OPENAI_API_KEY

from datetime import date

from storage import (
    get_user_profile,
    get_user_kbju,
    get_food_diary,
    get_water_amount,
    get_workout_history,
    get_premium_status,
    get_ai_coach_usage,
    increment_ai_coach_usage,
)

# ==========================================
#               ROUTER
# ==========================================

router = Router()

client = OpenAI(
    api_key=OPENAI_API_KEY,
    timeout=60
)


class AiCoachForm(StatesGroup):

    question = State()


# ==========================================
#              КЛАВИАТУРА AI КОУЧА
# ==========================================

def ai_coach_keyboard(is_premium=False):

    if is_premium:

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💬 Задать вопрос",
                        callback_data="ask_ai_coach"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🏋️ Тренировки",
                        callback_data="ai_workout"
                    ),
                    InlineKeyboardButton(
                        text="🍽 Питание",
                        callback_data="ai_food"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📈 Анализ прогресса",
                        callback_data="ai_progress"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="😴 Восстановление",
                        callback_data="ai_recovery"
                    ),
                    InlineKeyboardButton(
                        text="🔥 Мотивация",
                        callback_data="ai_motivation"
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

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Задать вопрос",
                    callback_data="ask_ai_coach"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏋️ Тренировки",
                    callback_data="ai_workout"
                ),
                InlineKeyboardButton(
                    text="🍽 Питание",
                    callback_data="ai_food"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💎 Анализ прогресса",
                    callback_data="ai_progress"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💎 Восстановление",
                    callback_data="ai_recovery"
                ),
                InlineKeyboardButton(
                    text="💎 Мотивация",
                    callback_data="ai_motivation"
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
#              AI КОУЧ
# ==========================================

@router.callback_query(F.data == "ai_coach")
async def ai_coach_handler(callback: CallbackQuery):

    try:
        await callback.message.delete()
    except Exception:
        pass

    is_premium = get_premium_status(
        callback.from_user.id
    )

    today = str(date.today())

    if is_premium:

        tariff_text = "💎 <b>Тариф:</b> Premium"
        limit_text = "♾️ <b>AI Коуч:</b> безлимит"

    else:

        used_today = get_ai_coach_usage(
            callback.from_user.id,
            today
        )

        left_today = 3 - used_today

        if left_today < 0:
            left_today = 0

        tariff_text = "🆓 <b>Тариф:</b> Free"
        limit_text = f"💬 Доступно сегодня: {left_today}/3"

    await callback.message.answer(
    "🤖 <b>AI КОУЧ</b>\n\n"

    "Твой персональный AI-тренер и помощник\n"
    "по тренировкам, питанию и восстановлению.\n\n"

    "━━━━━━━━━━━━━━\n\n"

    f"{tariff_text}\n"
    f"{limit_text}\n\n"

    "━━━━━━━━━━━━━━\n\n"

    "🎯 Чем могу помочь:\n\n"

    "🏋️ Улучшить тренировки\n"
    "🍽 Скорректировать питание\n"
    "📈 Оценить прогресс\n"
    "😴 Подсказать по восстановлению\n\n",
        reply_markup=ai_coach_keyboard(is_premium),
        parse_mode="HTML"
    )

    await callback.answer()



# ==========================================
#         ЗАДАТЬ ВОПРОС AI КОУЧУ
# ==========================================

@router.callback_query(F.data == "ask_ai_coach")
async def ask_ai_coach_handler(
    callback: CallbackQuery,
    state: FSMContext
    ):

    try:
        await callback.message.delete()
    except Exception:
        pass

    question_message = await callback.message.answer(
    "💬 <b>Задать вопрос AI Коучу</b>\n\n"
    "Напиши свой вопрос по питанию, тренировкам, прогрессу или восстановлению.\n\n"
    "<i>Например: почему вес стоит или как набрать массу?</i>",
    parse_mode="HTML"
    )

    await state.update_data(
    last_bot_message_id=question_message.message_id
    )

    await state.set_state(
        AiCoachForm.question
    )

    await callback.answer()


# ==========================================
#        ОБРАБОТКА ВОПРОСА AI КОУЧУ
# ==========================================

@router.message(AiCoachForm.question)
async def process_ai_coach_question(
    message: Message,
    state: FSMContext
):

    question = message.text

    try:
        await message.delete()
    except Exception:
        pass

    # ==========================================
    #      УДАЛЯЕМ СООБЩЕНИЕ "ЗАДАТЬ ВОПРОС"
    # ==========================================

    data = await state.get_data()

    last_bot_message_id = data.get("last_bot_message_id")

    if last_bot_message_id:

        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=last_bot_message_id
            )
        except Exception:
            pass

    # ==========================================
    #        ЛИМИТ AI КОУЧА ДЛЯ FREE
    # ==========================================

    today = str(date.today())

    is_premium = get_premium_status(
        message.from_user.id
    )

    if not is_premium:

        used_today = get_ai_coach_usage(
            message.from_user.id,
            today
        )

        if used_today >= 3:

            await message.answer(
                "💎 <b>Лимит Free исчерпан</b>\n\n"
                "Сегодня ты уже использовал <b>3 из 3</b> вопроса AI Коучу.\n\n"
                "Premium откроет:\n"
                "• безлимитные вопросы AI Коучу\n"
                "• анализ прогресса\n"
                "• восстановление\n"
                "• мотивацию\n"
                "• расширенные рекомендации Gym AI\n\n"
                "Чтобы продолжить — активируй Premium.",
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
                                text="🤖 Назад к AI Коучу",
                                callback_data="ai_coach"
                            )
                        ],
                    ]
                ),
                parse_mode="HTML"
            )

            await state.clear()
            return

    # ==========================================
    #        ПОЛУЧАЕМ ДАННЫЕ ПОЛЬЗОВАТЕЛЯ
    # ==========================================

    profile = get_user_profile(message.from_user.id)
    kbju = get_user_kbju(message.from_user.id)
    food_diary = get_food_diary(message.from_user.id)
    workout_history = get_workout_history(message.from_user.id)

    water_ml = get_water_amount(
        message.from_user.id,
        today
    )

    today_food = [
        meal for meal in food_diary
        if meal.get("date") == today
    ]

    # ==========================================
    #             LOADING MESSAGE
    # ==========================================

    loading_message = await message.answer(
        "🤖 <b>AI Коуч думает...</b>\n\n"
        "Анализирую твой вопрос и персональные данные.",
        parse_mode="HTML"
    )

    # ==========================================
    #             OPENAI ЗАПРОС
    # ==========================================

    try:

        response = client.responses.create(
            model="gpt-4.1-mini",
            input=(
                "Ты персональный AI-фитнес коуч в Telegram-боте Gym AI.\n"
                "Отвечай на русском языке, понятно, уверенно и полезно.\n"
                "Учитывай профиль пользователя, питание, КБЖУ, воду и тренировки.\n"
                "Не ставь диагнозы и не заменяй врача.\n"
                "Если вопрос связан со здоровьем, болью, травмами или заболеваниями — "
                "мягко рекомендуй обратиться к врачу или специалисту.\n\n"

                "ДАННЫЕ ПОЛЬЗОВАТЕЛЯ:\n"
                f"Профиль: {profile}\n"
                f"КБЖУ: {kbju}\n"
                f"Питание сегодня: {today_food}\n"
                f"Вода сегодня: {water_ml} мл\n"
                f"Последние тренировки: {workout_history[-5:]}\n\n"

                "ВОПРОС ПОЛЬЗОВАТЕЛЯ:\n"
                f"{question}\n\n"

                "ФОРМАТ ОТВЕТА:\n\n"
                "🤖 <b>Ответ Gym AI Коуча</b>\n\n"
                "Дай персональный ответ коротко и по делу.\n"
                "Если у пользователя не хватает данных, скажи, какие данные стоит заполнить.\n\n"
                "Не используй Markdown. Используй HTML <b>."
            )
        )

    except Exception as e:

        print("OPENAI AI COACH QUESTION ERROR:", e)

        try:
            await loading_message.delete()
        except Exception:
            pass

        await message.answer(
            "⚠️ <b>AI Коуч временно не ответил</b>\n\n"
            "Попробуй задать вопрос ещё раз через пару секунд.",
            reply_markup=ai_coach_keyboard(is_premium),
            parse_mode="HTML"
        )

        await state.clear()
        return

    # ==========================================
    #          УДАЛЯЕМ LOADING MESSAGE
    # ==========================================

    try:
        await loading_message.delete()
    except Exception:
        pass

    # ==========================================
    #          ОЧИЩАЕМ HTML
    # ==========================================

    result_text = (
        response.output_text
        .replace("<br>", "\n")
        .replace("<br/>", "\n")
        .replace("<br />", "\n")
    )

    # ==========================================
    #          ОБНОВЛЯЕМ ЛИМИТ
    # ==========================================

    if not is_premium:

        increment_ai_coach_usage(
            message.from_user.id,
            today
        )

        used_today = get_ai_coach_usage(
            message.from_user.id,
            today
        )

        limit_text = (
            f"\n\n🆓 <b>Free лимит:</b> {used_today}/3 вопроса сегодня"
        )

    else:

        limit_text = (
            "\n\n💎 <b>Premium:</b> безлимитный AI Коуч"
        )

    # ==========================================
    #          ОТПРАВЛЯЕМ ОТВЕТ
    # ==========================================

    await message.answer(
        result_text + limit_text,
        reply_markup=ai_coach_keyboard(is_premium),
        parse_mode="HTML"
    )

    await state.clear()



# ==========================================
#          AI АНАЛИЗ ПРОГРЕССА
# ==========================================

@router.callback_query(F.data == "ai_progress")
async def ai_progress_handler(callback: CallbackQuery):

    try:
        await callback.message.delete()
    except Exception:
        pass

    is_premium = get_premium_status(
        callback.from_user.id
    )

    if not is_premium:

        await callback.message.answer(
            "💎 <b>Анализ прогресса доступен в Premium</b>\n\n"
            "Premium откроет:\n"
            "• анализ тренировок\n"
            "• анализ питания\n"
            "• оценку воды и восстановления\n"
            "• персональные выводы Gym AI\n\n"
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
                            text="🤖 Назад к AI Коучу",
                            callback_data="ai_coach"
                        )
                    ],
                ]
            ),
            parse_mode="HTML"
        )

        await callback.answer()
        return

    profile = get_user_profile(callback.from_user.id)
    kbju = get_user_kbju(callback.from_user.id)
    food_diary = get_food_diary(callback.from_user.id)
    workout_history = get_workout_history(callback.from_user.id)

    today = str(date.today())

    water_ml = get_water_amount(
        callback.from_user.id,
        today
    )

    today_food = [
        meal for meal in food_diary
        if meal.get("date") == today
    ]

    loading_message = await callback.message.answer(
        "📈 <b>Gym AI анализирует прогресс...</b>\n\n"
        "Сравниваю питание, воду, тренировки и профиль.",
        parse_mode="HTML"
    )

    try:

        response = client.responses.create(
            model="gpt-4.1-mini",
            input=(
                "Ты профессиональный AI-фитнес коуч Gym AI.\n"
                "Сделай комплексный анализ прогресса пользователя на русском языке.\n\n"

                "ТВОЯ ЗАДАЧА:\n"
                "Оцени не отдельный параметр, а общую картину прогресса.\n"
                "Смотри на питание, воду, тренировки, профиль и цель пользователя.\n"
                "Дай короткие, практичные и честные выводы.\n\n"

                "УЧИТЫВАЙ:\n"
                "- цель пользователя\n"
                "- профиль пользователя\n"
                "- КБЖУ\n"
                "- питание за сегодня\n"
                "- воду за сегодня\n"
                "- историю последних тренировок\n"
                "- если данных мало — честно скажи, что полноценный анализ пока ограничен\n\n"

                "НЕ ДЕЛАЙ:\n"
                "- не ставь диагнозы\n"
                "- не обещай медицинские результаты\n"
                "- не делай категоричные выводы без данных\n"
                "- не используй сложные термины без объяснения\n\n"

                "ДАННЫЕ ПОЛЬЗОВАТЕЛЯ:\n"
                f"Профиль: {profile}\n\n"
                f"КБЖУ: {kbju}\n\n"
                f"Питание за сегодня: {today_food}\n\n"
                f"Вода за сегодня: {water_ml} мл\n\n"
                f"Последние тренировки: {workout_history[-5:]}\n\n"

                "ФОРМАТ ОТВЕТА:\n\n"

                "📈 <b>AI анализ прогресса</b>\n\n"

                "🏋️ <b>Тренировки</b>\n"
                "Оцени тренировки кратко. Если данных мало — скажи об этом.\n\n"

                "🍽 <b>Питание</b>\n"
                "Оцени питание относительно КБЖУ и цели.\n\n"

                "💧 <b>Вода</b>\n"
                "Оцени водный баланс.\n\n"

                "📊 <b>Общая оценка</b>\n"
                "Напиши, движется ли пользователь в правильном направлении.\n\n"

                "✅ <b>Сильные стороны</b>\n"
                "• ...\n"
                "• ...\n\n"

                "⚠️ <b>Что мешает прогрессу</b>\n"
                "• ...\n"
                "• ...\n\n"

                "🎯 <b>Фокус на ближайшие 7 дней</b>\n"
                "• ...\n"
                "• ...\n"
                "• ...\n\n"

                "🚀 <b>Вывод Gym AI</b>\n"
                "Короткий мотивирующий, но реалистичный вывод.\n\n"

                "Пиши коротко, понятно и по делу.\n"
                "Не используй Markdown. Используй только HTML <b>."
            )
        )

    except Exception as e:

        print("OPENAI AI PROGRESS ERROR:", e)

        try:
            await loading_message.delete()
        except Exception:
            pass

        await callback.message.answer(
            "⚠️ <b>AI Коуч временно не смог сделать анализ</b>\n\n"
            "Попробуй ещё раз через пару секунд.",
            reply_markup=ai_coach_keyboard(is_premium),
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
        reply_markup=ai_coach_keyboard(is_premium),
        parse_mode="HTML"
    )

    await callback.answer()


# ==========================================
#          AI СОВЕТЫ ПО ПИТАНИЮ
# ==========================================

@router.callback_query(F.data == "ai_food")
async def ai_nutrition_handler(callback: CallbackQuery):

    try:
        await callback.message.delete()
    except Exception:
        pass

    is_premium = get_premium_status(
        callback.from_user.id
    )

    profile = get_user_profile(
        callback.from_user.id
    )

    kbju = get_user_kbju(
        callback.from_user.id
    )

    food_diary = get_food_diary(
        callback.from_user.id
    )

    today = str(date.today())

    today_food = [
        meal for meal in food_diary
        if meal.get("date") == today
    ]

    water_ml = get_water_amount(
        callback.from_user.id,
        today
    )

    loading_message = await callback.message.answer(
        "🍽 <b>Gym AI анализирует питание...</b>\n\n"
        "Смотрю КБЖУ, дневник питания и воду за сегодня.",
        parse_mode="HTML"
    )

    try:

        response = client.responses.create(
            model="gpt-4.1-mini",
            input=(
                "Ты профессиональный AI-нутрициолог Gym AI.\n"
                "Дай пользователю персональные рекомендации по питанию на русском языке.\n\n"

                "ТВОЯ ЗАДАЧА:\n"
                "Не просто пересказать данные, а дать понятные действия по питанию.\n"
                "Оцени рацион, КБЖУ, воду и соответствие цели пользователя.\n\n"

                "УЧИТЫВАЙ:\n"
                "- профиль пользователя\n"
                "- цель пользователя\n"
                "- рассчитанные КБЖУ\n"
                "- питание за сегодня\n"
                "- воду за сегодня\n"
                "- если данных мало — честно скажи, что данных пока недостаточно\n\n"

                "НЕ ДЕЛАЙ:\n"
                "- не ставь диагнозы\n"
                "- не обещай медицинский результат\n"
                "- не назначай лечебные диеты\n"
                "- не делай жесткие выводы без данных\n\n"

                "ДАННЫЕ ПОЛЬЗОВАТЕЛЯ:\n"
                f"Профиль: {profile}\n\n"
                f"КБЖУ: {kbju}\n\n"
                f"Питание за сегодня: {today_food}\n\n"
                f"Вода за сегодня: {water_ml} мл\n\n"

                "ФОРМАТ ОТВЕТА:\n\n"
                "🍽 <b>AI рекомендации по питанию</b>\n\n"

                "📊 <b>Общая оценка</b>\n"
                "Коротко оцени питание за сегодня.\n\n"

                "✅ <b>Что хорошо</b>\n"
                "• ...\n"
                "• ...\n\n"

                "⚠️ <b>Что улучшить</b>\n"
                "• ...\n"
                "• ...\n\n"

                "🎯 <b>Что сделать сегодня</b>\n"
                "• ...\n"
                "• ...\n"
                "• ...\n\n"

                "💡 <b>Совет Gym AI</b>\n"
                "Один короткий практический совет по питанию.\n\n"

                "Пиши коротко, понятно и по делу.\n"
                "Не используй Markdown. Используй только HTML <b>."
            )
        )

    except Exception as e:

        print("OPENAI AI NUTRITION ERROR:", e)

        try:
            await loading_message.delete()
        except Exception:
            pass

        await callback.message.answer(
            "⚠️ <b>AI Коуч временно не смог проанализировать питание</b>\n\n"
            "Попробуй ещё раз через пару секунд.",
            reply_markup=ai_coach_keyboard(is_premium),
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
        reply_markup=ai_coach_keyboard(is_premium),
        parse_mode="HTML"
    )

    await callback.answer()


# ==========================================
#          AI СОВЕТЫ ПО ТРЕНИРОВКАМ
# ==========================================

@router.callback_query(F.data == "ai_workout")
async def ai_workout_handler(callback: CallbackQuery):

    try:
        await callback.message.delete()
    except Exception:
        pass

    is_premium = get_premium_status(
        callback.from_user.id
    )

    profile = get_user_profile(
        callback.from_user.id
    )

    workout_history = get_workout_history(
        callback.from_user.id
    )

    loading_message = await callback.message.answer(
        "🏋️ <b>Gym AI анализирует тренировки...</b>\n\n"
        "Смотрю профиль, цель и последние тренировки.",
        parse_mode="HTML"
    )

    try:

        response = client.responses.create(
            model="gpt-4.1-mini",
            input=(
                "Ты профессиональный AI-фитнес тренер Gym AI.\n"
                "Дай пользователю персональные рекомендации по тренировкам на русском языке.\n\n"

                "ТВОЯ ЗАДАЧА:\n"
                "Не просто пересказать данные, а дать понятные действия.\n"
                "Оцени тренировки пользователя, цель, уровень нагрузки и регулярность.\n\n"

                "УЧИТЫВАЙ:\n"
                "- цель пользователя\n"
                "- пол, возраст, рост и вес, если они есть в профиле\n"
                "- историю последних тренировок\n"
                "- регулярность тренировок\n"
                "- возможные ограничения, если они есть в профиле\n"
                "- если истории тренировок мало — честно скажи, что данных пока недостаточно\n\n"

                "НЕ ДЕЛАЙ:\n"
                "- не ставь диагнозы\n"
                "- не обещай медицинский результат\n"
                "- не рекомендуй опасные нагрузки\n"
                "- не делай выводы, если данных нет\n\n"

                "ДАННЫЕ ПОЛЬЗОВАТЕЛЯ:\n"
                f"Профиль: {profile}\n\n"
                f"Последние тренировки: {workout_history[-5:]}\n\n"

                "ФОРМАТ ОТВЕТА:\n\n"
                "🏋️ <b>AI рекомендации по тренировкам</b>\n\n"

                "📊 <b>Общая оценка</b>\n"
                "Коротко оцени текущую тренировочную ситуацию.\n\n"

                "✅ <b>Что хорошо</b>\n"
                "• ...\n"
                "• ...\n\n"

                "⚠️ <b>Что улучшить</b>\n"
                "• ...\n"
                "• ...\n\n"

                "🎯 <b>Следующий шаг</b>\n"
                "• ...\n"
                "• ...\n"
                "• ...\n\n"

                "💡 <b>Совет Gym AI</b>\n"
                "Один короткий практический совет на ближайшую тренировку.\n\n"

                "Пиши коротко, понятно и по делу.\n"
                "Не используй Markdown. Используй только HTML <b>."
            )
        )

    except Exception as e:

        print("OPENAI AI WORKOUT ERROR:", e)

        try:
            await loading_message.delete()
        except Exception:
            pass

        await callback.message.answer(
            "⚠️ <b>AI Коуч временно не смог проанализировать тренировки</b>\n\n"
            "Попробуй ещё раз через пару секунд.",
            reply_markup=ai_coach_keyboard(is_premium),
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
        reply_markup=ai_coach_keyboard(is_premium),
        parse_mode="HTML"
    )

    await callback.answer()



# ==========================================
#          AI СОВЕТЫ ПО ВОССТАНОВЛЕНИЮ
# ==========================================

@router.callback_query(F.data == "ai_recovery")
async def ai_recovery_handler(callback: CallbackQuery):

    try:
        await callback.message.delete()
    except Exception:
        pass

    is_premium = get_premium_status(
        callback.from_user.id
    )

    if not is_premium:

        await callback.message.answer(
            "💎 <b>Восстановление доступно в Premium</b>\n\n"
            "Premium откроет:\n"
            "• рекомендации по сну\n"
            "• анализ восстановления\n"
            "• советы по нагрузке\n"
            "• персональные рекомендации Gym AI\n\n"
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
                            text="🤖 Назад к AI Коучу",
                            callback_data="ai_coach"
                        )
                    ]
                ]
            ),
            parse_mode="HTML"
        )

        await callback.answer()
        return

    profile = get_user_profile(
        callback.from_user.id
    )

    workout_history = get_workout_history(
        callback.from_user.id
    )

    food_diary = get_food_diary(
        callback.from_user.id
    )

    today = str(date.today())

    today_food = [
        meal for meal in food_diary
        if meal.get("date") == today
    ]

    loading_message = await callback.message.answer(
        "😴 <b>Gym AI анализирует восстановление...</b>\n\n"
        "Смотрю тренировки, питание и общую нагрузку.",
        parse_mode="HTML"
    )

    try:

        response = client.responses.create(
            model="gpt-4.1-mini",
            input=(
                "Ты профессиональный AI-фитнес коуч Gym AI.\n"
                "Проанализируй восстановление пользователя на русском языке.\n\n"

                "ТВОЯ ЗАДАЧА:\n"
                "Оцени восстановление не как врач, а как фитнес-коуч.\n"
                "Смотри на тренировки, питание, регулярность и возможную усталость.\n"
                "Дай короткие, безопасные и практичные рекомендации.\n\n"

                "УЧИТЫВАЙ:\n"
                "- профиль пользователя\n"
                "- последние тренировки\n"
                "- питание за сегодня\n"
                "- регулярность нагрузки\n"
                "- если данных мало — честно скажи, что анализ ограничен\n\n"

                "НЕ ДЕЛАЙ:\n"
                "- не ставь диагнозы\n"
                "- не назначай лечение\n"
                "- не обещай медицинский результат\n"
                "- если есть боль, травмы или сильная усталость — мягко рекомендуй обратиться к специалисту\n\n"

                "ДАННЫЕ ПОЛЬЗОВАТЕЛЯ:\n"
                f"Профиль: {profile}\n\n"
                f"Питание за сегодня: {today_food}\n\n"
                f"Последние тренировки: {workout_history[-5:]}\n\n"

                "ФОРМАТ ОТВЕТА:\n\n"
                "😴 <b>AI анализ восстановления</b>\n\n"

                "📊 <b>Общая оценка</b>\n"
                "Коротко оцени восстановление и нагрузку.\n\n"

                "✅ <b>Что помогает восстановлению</b>\n"
                "• ...\n"
                "• ...\n\n"

                "⚠️ <b>Что может мешать</b>\n"
                "• ...\n"
                "• ...\n\n"

                "🎯 <b>Что сделать сегодня</b>\n"
                "• ...\n"
                "• ...\n"
                "• ...\n\n"

                "💡 <b>Совет Gym AI</b>\n"
                "Один короткий практический совет по восстановлению.\n\n"

                "Пиши коротко, понятно и по делу.\n"
                "Не используй Markdown. Используй только HTML <b>."
            )
        )

    except Exception as e:

        print("OPENAI AI RECOVERY ERROR:", e)

        try:
            await loading_message.delete()
        except Exception:
            pass

        await callback.message.answer(
            "⚠️ <b>AI Коуч временно не смог проанализировать восстановление</b>\n\n"
            "Попробуй ещё раз через пару секунд.",
            reply_markup=ai_coach_keyboard(is_premium),
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
        reply_markup=ai_coach_keyboard(is_premium),
        parse_mode="HTML"
    )

    await callback.answer()


# ==========================================
#              AI МОТИВАЦИЯ
# ==========================================

@router.callback_query(F.data == "ai_motivation")
async def ai_motivation_handler(callback: CallbackQuery):

    try:
        await callback.message.delete()
    except Exception:
        pass

    is_premium = get_premium_status(
        callback.from_user.id
    )

    if not is_premium:

        await callback.message.answer(
            "💎 <b>Мотивация доступна в Premium</b>\n\n"
            "Premium откроет:\n"
            "• персональную мотивацию\n"
            "• поддержку Gym AI\n"
            "• напоминание о целях\n"
            "• рекомендации для сохранения дисциплины\n\n"
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
                            text="🤖 Назад к AI Коучу",
                            callback_data="ai_coach"
                        )
                    ]
                ]
            ),
            parse_mode="HTML"
        )

        await callback.answer()
        return

    profile = get_user_profile(
        callback.from_user.id
    )

    kbju = get_user_kbju(
        callback.from_user.id
    )

    food_diary = get_food_diary(
        callback.from_user.id
    )

    workout_history = get_workout_history(
        callback.from_user.id
    )

    today = str(date.today())

    today_food = [
        meal for meal in food_diary
        if meal.get("date") == today
    ]

    loading_message = await callback.message.answer(
        "🔥 <b>Gym AI готовит мотивацию...</b>\n\n"
        "Смотрю цель, питание и последние тренировки.",
        parse_mode="HTML"
    )

    try:

        response = client.responses.create(
            model="gpt-4.1-mini",
            input=(
                "Ты мотивирующий AI-фитнес коуч Gym AI.\n"
                "Дай пользователю короткую, сильную и персональную мотивацию на русском языке.\n\n"

                "ТВОЯ ЗАДАЧА:\n"
                "Мотивация должна быть персональной, не шаблонной.\n"
                "Опирайся на цель пользователя, питание и тренировки.\n"
                "Поддержи пользователя, но не обещай быстрых результатов.\n"
                "Тон: уверенный, спокойный, заряжающий.\n\n"

                "УЧИТЫВАЙ:\n"
                "- профиль пользователя\n"
                "- цель пользователя\n"
                "- КБЖУ\n"
                "- питание за сегодня\n"
                "- последние тренировки\n"
                "- если данных мало — сделай универсальную, но честную мотивацию\n\n"

                "НЕ ДЕЛАЙ:\n"
                "- не используй токсичную мотивацию\n"
                "- не дави на чувство вины\n"
                "- не обещай быстрые изменения тела\n"
                "- не ставь диагнозы\n\n"

                "ДАННЫЕ ПОЛЬЗОВАТЕЛЯ:\n"
                f"Профиль: {profile}\n\n"
                f"КБЖУ: {kbju}\n\n"
                f"Питание за сегодня: {today_food}\n\n"
                f"Последние тренировки: {workout_history[-5:]}\n\n"

                "ФОРМАТ ОТВЕТА:\n\n"
                "🔥 <b>Мотивация Gym AI</b>\n\n"

                "Напиши 5–7 коротких предложений.\n"
                "Сделай текст живым, уверенным и персональным.\n"
                "В конце добавь одну сильную фразу отдельной строкой.\n\n"

                "Не используй Markdown. Используй только HTML <b>."
            )
        )

    except Exception as e:

        print("OPENAI AI MOTIVATION ERROR:", e)

        try:
            await loading_message.delete()
        except Exception:
            pass

        await callback.message.answer(
            "⚠️ <b>AI Коуч временно не смог подготовить мотивацию</b>\n\n"
            "Попробуй ещё раз через пару секунд.",
            reply_markup=ai_coach_keyboard(is_premium),
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
        reply_markup=ai_coach_keyboard(is_premium),
        parse_mode="HTML"
    )

    await callback.answer()