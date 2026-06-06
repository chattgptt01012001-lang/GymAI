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
from datetime import date

from storage import (
    get_user_profile,
    get_user_kbju,
    save_user_profile,
    save_user_kbju,
    save_inbody_result,
    get_inbody_result,
    get_inbody_history,
    get_inbody_result,
    delete_inbody_entry,
    get_premium_status,
)

from aiogram.types import FSInputFile
from openai import OpenAI
from config import OPENAI_API_KEY

import os
import base64
import fitz


# ==========================================
#            СОЗДАНИЕ ROUTER
# ==========================================

router = Router()


# ==========================================
#            OPENAI CLIENT
# ==========================================

client = OpenAI(
    api_key=OPENAI_API_KEY,
    timeout=60
)


# ==========================================
#        СОСТОЯНИЯ АНКЕТЫ ПРОФИЛЯ
# ==========================================

class ProfileEditForm(StatesGroup):

    gender = State()
    age = State()
    height = State()
    weight = State()
    goal = State()
    activity = State()
    training_experience = State()
    body_change_speed = State()
    limitations = State()
    desired_result = State()


# ==========================================
#           СОСТОЯНИЯ INBODY
# ==========================================

class InBodyForm(StatesGroup):

    waiting_for_inbody = State()


# ==========================================
#              КЛАВИАТУРЫ
# ==========================================

def profile_menu_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[

    [
        InlineKeyboardButton(
            text="📸 Загрузить InBody",
            callback_data="upload_inbody"
        )
    ],
    [
        InlineKeyboardButton(
            text="📈 История InBody",
            callback_data="inbody_history"
    )
    ],
    [
        InlineKeyboardButton(
            text="💎 AI анализ InBody",
            callback_data="ai_inbody_analysis"
    )
    ],
    [
        InlineKeyboardButton(
            text="✏️ Изменить данные",
            callback_data="profile_edit_start"
        )
    ],

    [
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="back_to_main_menu"
        )
    ]

        ]
    )


def gender_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Мужчина", callback_data="profile_gender_male"),
                InlineKeyboardButton(text="Женщина", callback_data="profile_gender_female"),
            ]
        ]
    )


def goal_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Похудение", callback_data="profile_goal_loss")],
            [InlineKeyboardButton(text="Поддержание формы", callback_data="profile_goal_maintain")],
            [InlineKeyboardButton(text="Набор массы", callback_data="profile_goal_gain")],
        ]
    )


def activity_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛋 Сижу дома, ничего не делаю", callback_data="profile_activity_low")],
            [InlineKeyboardButton(text="🚶 Легкая активность 1–2 раза в неделю", callback_data="profile_activity_light")],
            [InlineKeyboardButton(text="🏃 Средняя активность 3–4 раза в неделю", callback_data="profile_activity_medium")],
            [InlineKeyboardButton(text="🏋️ Высокая активность 5–7 раз в неделю", callback_data="profile_activity_high")],
            [InlineKeyboardButton(text="💪 Физическая работа + спорт", callback_data="profile_activity_very_high")],
        ]
    )


def training_experience_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Новичок", callback_data="profile_experience_beginner")],
            [InlineKeyboardButton(text="Средний уровень", callback_data="profile_experience_intermediate")],
            [InlineKeyboardButton(text="Опытный", callback_data="profile_experience_advanced")],
        ]
    )


def body_change_speed_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🐢 Плавно", callback_data="profile_speed_slow")],
            [InlineKeyboardButton(text="⚡ Умеренно", callback_data="profile_speed_medium")],
            [InlineKeyboardButton(text="🔥 Быстро", callback_data="profile_speed_fast")],
            [InlineKeyboardButton(text="☠️ Экстремальная весогонка", callback_data="profile_speed_extreme")],
        ]
    )


def limitations_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Нет ограничений", callback_data="profile_limitations_no")],
            [InlineKeyboardButton(text="Есть ограничения", callback_data="profile_limitations_yes")],
        ]
    )


# ==========================================
#        УДАЛЕНИЕ ПОСЛЕДНЕГО ВОПРОСА
# ==========================================

async def delete_last_bot_message(message_or_callback, state: FSMContext):

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

def calculate_kbju(age, gender, height, weight, goal, activity, body_change_speed):

    age = int(age)
    height = int(height)
    weight = float(weight)

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
        "medium": 400,
        "fast": 600,
        "extreme": 900,
    }

    calories = bmr * activity_map[activity]
    correction = speed_map[body_change_speed]

    if goal == "loss":
        calories -= correction
    elif goal == "gain":
        calories += correction

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
#              ПОКАЗ ПРОФИЛЯ
# ==========================================

@router.callback_query(F.data == "menu_profile")
async def open_profile(callback: CallbackQuery):

    try:
        await callback.message.delete()
    except Exception:
        pass

    profile = get_user_profile(
        callback.from_user.id
    )

    kbju = get_user_kbju(
        callback.from_user.id
    )

    # ==========================================
    #        ЕСЛИ ПРОФИЛЬ НЕ ЗАПОЛНЕН
    # ==========================================

    if not profile:

        await callback.message.answer(
            "👤 <b>МОЙ ПРОФИЛЬ</b>\n\n"
            "Профиль пока не заполнен.\n\n"
            "Нажми кнопку ниже, чтобы заполнить данные.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="📝 Заполнить профиль",
                            callback_data="profile_edit_start"
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
        return

    # ==========================================
    #              ПЕРЕВОДЫ
    # ==========================================

    gender_map = {
        "male": "Мужчина",
        "female": "Женщина",
    }

    goal_map = {
        "loss": "Похудение",
        "gain": "Набор массы",
        "maintain": "Поддержание формы",
    }

    activity_map = {
        "low": "Низкая",
        "light": "Легкая",
        "medium": "Средняя",
        "high": "Высокая",
        "very_high": "Очень высокая",
    }

    limitations_map = {
        "no": "Нет ограничений",
        "yes": "Есть ограничения",
    }

    # ==========================================
    #              INBODY
    # ==========================================

    inbody = get_inbody_result(
        callback.from_user.id
    )

    if inbody and isinstance(inbody, dict):

        inbody_text = (
            "📊 <b>InBody</b>\n\n"
            f"🟢 Последний отчет: <b>{inbody.get('date', '—')}</b>\n\n"
            f"{inbody.get('text', 'Нет данных')}"
        )

    else:

        inbody_text = (
            "📊 <b>InBody</b>\n\n"
            "❌ Данные InBody пока не выгружены"
        )

    # ==========================================
    #              КБЖУ
    # ==========================================

    if kbju:

        kbju_text = (
            "🔥 <b>Твои нормы КБЖУ</b>\n\n"
            f"🍽 Калории: <b>{kbju['calories']} ккал</b>\n"
            f"🥩 Белки: <b>{kbju['protein']} г</b>\n"
            f"🥑 Жиры: <b>{kbju['fat']} г</b>\n"
            f"🍚 Углеводы: <b>{kbju['carbs']} г</b>"
        )

    else:

        kbju_text = (
            "🔥 <b>Твои нормы КБЖУ</b>\n\n"
            "КБЖУ пока не рассчитано."
        )

    # ==========================================
    #              ТЕКСТ ПРОФИЛЯ
    # ==========================================

    profile_text = (
        "👤 <b>МОЙ ПРОФИЛЬ</b>\n\n"

        "━━━━━━━━━━━━━━\n\n"

        "📋 <b>Основные данные</b>\n\n"

        f"👨 Пол: <b>{gender_map.get(profile.get('gender'), profile.get('gender', '—'))}</b>\n"
        f"🎂 Возраст: <b>{profile.get('age', '—')}</b>\n"
        f"📏 Рост: <b>{profile.get('height', '—')} см</b>\n"
        f"⚖️ Вес: <b>{profile.get('weight', '—')} кг</b>\n\n"

        f"🎯 Цель: <b>{goal_map.get(profile.get('goal'), profile.get('goal', '—'))}</b>\n"
        f"🏃 Активность: <b>{activity_map.get(profile.get('activity'), profile.get('activity', '—'))}</b>\n"
    )

    limitations = limitations_map.get(
        profile.get("limitations"),
        profile.get("limitations", "")
    )

    if limitations and limitations != "Нет ограничений":

        profile_text += (
            f"\n⚠️ Ограничения: <b>{limitations}</b>\n"
        )

    profile_text += (
        "\n━━━━━━━━━━━━━━\n\n"
        f"{kbju_text}\n\n"
        "━━━━━━━━━━━━━━\n\n"
        f"{inbody_text}"
    )

    # ==========================================
    #          ОТПРАВКА ПРОФИЛЯ
    # ==========================================

    await callback.message.answer(
        profile_text,
        reply_markup=profile_menu_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


# ==========================================
#          СТАРТ ИЗМЕНЕНИЯ ПРОФИЛЯ
# ==========================================

@router.callback_query(F.data == "profile_edit_start")
async def profile_edit_start(callback: CallbackQuery, state: FSMContext):

    try:
        await callback.message.delete()
    except Exception:
        pass

    await state.clear()

    question = await callback.message.answer(
        "📋 <b>Вопрос 1/10</b>\n\n"
        "Начнем с самого главного: укажи пол.\n\n"
        "Так расчет КБЖУ будет максимально точным.",
        reply_markup=gender_keyboard(),
        parse_mode="HTML"
    )

    await state.update_data(last_bot_message_id=question.message_id)
    await state.set_state(ProfileEditForm.gender)

    await callback.answer()


# ==========================================
#             ВОПРОС 1 — ПОЛ
# ==========================================

@router.callback_query(ProfileEditForm.gender, F.data.startswith("profile_gender_"))
async def process_profile_gender(callback: CallbackQuery, state: FSMContext):

    await callback.message.delete()

    gender = callback.data.replace("profile_gender_", "")

    await state.update_data(gender=gender)

    question = await callback.message.answer(
        "📋 <b>Вопрос 2/10</b>\n\n"
        "Сколько тебе полных лет?\n\n"
        "<i>Например: 25</i>",
        parse_mode="HTML"
    )

    await state.update_data(last_bot_message_id=question.message_id)
    await state.set_state(ProfileEditForm.age)

    await callback.answer()


# ==========================================
#             ВОПРОС 2 — ВОЗРАСТ
# ==========================================

@router.message(ProfileEditForm.age)
async def process_profile_age(message: Message, state: FSMContext):

    if not message.text.isdigit():

        await message.answer(
            "Введи возраст числом.\n\n"
            "Например: 25"
        )

        return

    await delete_last_bot_message(message, state)
    await message.delete()

    await state.update_data(age=message.text)

    question = await message.answer(
        "📋 <b>Вопрос 3/10</b>\n\n"
        "Укажи свой рост в сантиметрах.\n\n"
        "<i>Например: 180</i>",
        parse_mode="HTML"
    )

    await state.update_data(last_bot_message_id=question.message_id)
    await state.set_state(ProfileEditForm.height)


# ==========================================
#             ВОПРОС 3 — РОСТ
# ==========================================

@router.message(ProfileEditForm.height)
async def process_profile_height(message: Message, state: FSMContext):

    if not message.text.isdigit():

        await message.answer(
            "Введи рост числом.\n\n"
            "Например: 180"
        )

        return

    await delete_last_bot_message(message, state)
    await message.delete()

    await state.update_data(height=message.text)

    question = await message.answer(
        "📋 <b>Вопрос 4/10</b>\n\n"
        "Укажи свой нынешний вес.\n\n"
        "<i>Например: 75 или 75.5</i>",
        parse_mode="HTML"
    )

    await state.update_data(last_bot_message_id=question.message_id)
    await state.set_state(ProfileEditForm.weight)


# ==========================================
#             ВОПРОС 4 — ВЕС
# ==========================================

@router.message(ProfileEditForm.weight)
async def process_profile_weight(message: Message, state: FSMContext):

    try:
        weight = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer(
            "Введи вес числом.\n\n"
            "Например: 75 или 75.5"
        )
        return

    await delete_last_bot_message(message, state)
    await message.delete()

    await state.update_data(weight=weight)

    question = await message.answer(
        "📋 <b>Вопрос 5/10</b>\n\n"
        "Какая у тебя основная цель?",
        reply_markup=goal_keyboard(),
        parse_mode="HTML"
    )

    await state.update_data(last_bot_message_id=question.message_id)
    await state.set_state(ProfileEditForm.goal)


# ==========================================
#             ВОПРОС 5 — ЦЕЛЬ
# ==========================================

@router.callback_query(ProfileEditForm.goal, F.data.startswith("profile_goal_"))
async def process_profile_goal(callback: CallbackQuery, state: FSMContext):

    await callback.message.delete()

    goal = callback.data.replace("profile_goal_", "")

    await state.update_data(goal=goal)

    question = await callback.message.answer(
        "📋 <b>Вопрос 6/10</b>\n\n"
        "Какой у тебя обычный уровень активности "
        "вне зала — работа, быт, шаги в течение дня?",
        reply_markup=activity_keyboard(),
        parse_mode="HTML"
    )

    await state.update_data(last_bot_message_id=question.message_id)
    await state.set_state(ProfileEditForm.activity)

    await callback.answer()


# ==========================================
#             ВОПРОС 6 — АКТИВНОСТЬ
# ==========================================

@router.callback_query(ProfileEditForm.activity, F.data.startswith("profile_activity_"))
async def process_profile_activity(callback: CallbackQuery, state: FSMContext):

    await callback.message.delete()

    activity = callback.data.replace("profile_activity_", "")

    await state.update_data(activity=activity)

    question = await callback.message.answer(
        "📋 <b>Вопрос 7/10</b>\n\n"
        "Какой у тебя опыт тренировок?",
        reply_markup=training_experience_keyboard(),
        parse_mode="HTML"
    )

    await state.update_data(last_bot_message_id=question.message_id)
    await state.set_state(ProfileEditForm.training_experience)

    await callback.answer()


# ==========================================
#          ВОПРОС 7 — ОПЫТ ТРЕНИРОВОК
# ==========================================

@router.callback_query(ProfileEditForm.training_experience, F.data.startswith("profile_experience_"))
async def process_profile_training_experience(callback: CallbackQuery, state: FSMContext):

    await callback.message.delete()

    training_experience = callback.data.replace("profile_experience_", "")

    await state.update_data(training_experience=training_experience)

    question = await callback.message.answer(
        "📋 <b>Вопрос 8/10</b>\n\n"
        "Какой темп изменения тела тебе ближе?",
        reply_markup=body_change_speed_keyboard(),
        parse_mode="HTML"
    )

    await state.update_data(last_bot_message_id=question.message_id)
    await state.set_state(ProfileEditForm.body_change_speed)

    await callback.answer()


# ==========================================
#          ВОПРОС 8 — ТЕМП ИЗМЕНЕНИЯ
# ==========================================

@router.callback_query(ProfileEditForm.body_change_speed, F.data.startswith("profile_speed_"))
async def process_profile_body_change_speed(callback: CallbackQuery, state: FSMContext):

    await callback.message.delete()

    body_change_speed = callback.data.replace("profile_speed_", "")

    await state.update_data(body_change_speed=body_change_speed)

    question = await callback.message.answer(
        "📋 <b>Вопрос 9/10</b>\n\n"
        "Есть ли у тебя ограничения, травмы или противопоказания?",
        reply_markup=limitations_keyboard(),
        parse_mode="HTML"
    )

    await state.update_data(last_bot_message_id=question.message_id)
    await state.set_state(ProfileEditForm.limitations)

    await callback.answer()


# ==========================================
#          ВОПРОС 9 — ОГРАНИЧЕНИЯ
# ==========================================

@router.callback_query(ProfileEditForm.limitations, F.data.startswith("profile_limitations_"))
async def process_profile_limitations(callback: CallbackQuery, state: FSMContext):

    await callback.message.delete()

    limitations = callback.data.replace("profile_limitations_", "")

    await state.update_data(limitations=limitations)

    question = await callback.message.answer(
        "📋 <b>Вопрос 10/10</b>\n\n"
        "Опиши желаемый результат.\n\n"
        "<i>Например: хочу похудеть на 5 кг, подтянуть тело и улучшить выносливость.</i>",
        parse_mode="HTML"
    )

    await state.update_data(last_bot_message_id=question.message_id)
    await state.set_state(ProfileEditForm.desired_result)

    await callback.answer()


# ==========================================
#          ВОПРОС 10 — ЖЕЛАЕМЫЙ РЕЗУЛЬТАТ
# ==========================================

@router.message(ProfileEditForm.desired_result)
async def process_profile_desired_result(message: Message, state: FSMContext):

    if len(message.text.strip()) < 3:

        await message.answer(
            "Напиши желаемый результат чуть подробнее."
        )

        return

    await delete_last_bot_message(message, state)
    await message.delete()

    await state.update_data(desired_result=message.text)

    data = await state.get_data()

    kbju = calculate_kbju(
        age=data["age"],
        gender=data["gender"],
        height=data["height"],
        weight=data["weight"],
        goal=data["goal"],
        activity=data["activity"],
        body_change_speed=data["body_change_speed"],
    )

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

    save_user_kbju(
        message.from_user.id,
        kbju
    )

    await message.answer(
        "✅ <b>Твой профиль Gym AI обновлен</b>\n\n"
        "Данные сохранены. Новое КБЖУ рассчитано 👇\n\n"
        f"🔥 Калории: <b>{kbju['calories']} ккал</b>\n"
        f"🥩 Белки: <b>{kbju['protein']} г</b>\n"
        f"🧈 Жиры: <b>{kbju['fat']} г</b>\n"
        f"🍚 Углеводы: <b>{kbju['carbs']} г</b>",
        reply_markup=profile_menu_keyboard(),
        parse_mode="HTML"
    )

    await state.clear()


# ==========================================
#            ЗАГРУЗКА INBODY
# ==========================================

@router.callback_query(F.data == "upload_inbody")
async def upload_inbody_handler(
    callback: CallbackQuery,
    state: FSMContext
):

    try:
        await callback.message.delete()
    except Exception:
        pass

    upload_message = await callback.message.answer(
        "📸 <b>Загрузка InBody</b>\n\n"
        "Отправь:\n"
        "• фото InBody\n"
        "или\n"
        "• PDF файл\n\n"
        "Gym AI автоматически проанализирует состав тела.",
        parse_mode="HTML"
    )

    await state.update_data(
        upload_message_id=upload_message.message_id
    )

    await state.set_state(
        InBodyForm.waiting_for_inbody
    )

    await callback.answer()


# ==========================================
#        PDF INBODY → IMAGE BASE64
# ==========================================

def pdf_to_base64_image(pdf_path):

    doc = fitz.open(pdf_path)

    page = doc[0]

    pix = page.get_pixmap(
        matrix=fitz.Matrix(2, 2)
    )

    image_path = pdf_path.replace(".pdf", ".png")

    pix.save(image_path)

    with open(image_path, "rb") as image_file:
        image_base64 = base64.b64encode(
            image_file.read()
        ).decode("utf-8")

    doc.close()

    os.remove(image_path)

    return f"data:image/png;base64,{image_base64}"


# ==========================================
#          ОБРАБОТКА INBODY ФОТО
# ==========================================

@router.message(InBodyForm.waiting_for_inbody)
async def process_inbody_photo(
    message: Message,
    state: FSMContext
):

    if not message.photo:

        await message.answer(
            "⚠️ Отправь фото или PDF InBody."
        )

        return

    data = await state.get_data()

    upload_message_id = data.get("upload_message_id")

    try:
        await message.delete()
    except Exception:
        pass

    if upload_message_id:

        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=upload_message_id
            )
        except Exception:
            pass

    loading_message = await message.answer(
        "🤖 <b>Gym AI анализирует InBody...</b>\n\n"
        "Считываю состав тела.",
        parse_mode="HTML"
    )

    # ==========================================
    #        ПОЛУЧАЕМ ФОТО ИЛИ PDF
    # ==========================================

    if message.photo:

        photo = message.photo[-1]

        file = await message.bot.get_file(
            photo.file_id
        )

        image_url = (
            f"https://api.telegram.org/file/bot"
            f"{message.bot.token}/{file.file_path}"
        )

    else:

        document = message.document

        if document.mime_type != "application/pdf":

            await loading_message.delete()

            await message.answer(
                "⚠️ Можно отправить только фото или PDF InBody.",
                parse_mode="HTML"
            )

            await state.clear()
            return

        file = await message.bot.get_file(
            document.file_id
        )

        file_path = f"inbody_{message.from_user.id}.pdf"

        await message.bot.download_file(
            file.file_path,
            destination=file_path
        )

        image_url = pdf_to_base64_image(file_path)

        os.remove(file_path)

    try:

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты анализируешь фото InBody / состава тела. "
                        "Ответь строго на русском языке. "
                        "Если показатель не найден — напиши 'не найдено'."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Проанализируй изображение InBody.\n\n"

                                "ВАЖНО:\n"
                                "Не придумывай значения.\n"
                                "Бери цифры только если они явно видны на изображении.\n"
                                "Висцеральный жир бери ТОЛЬКО из строки или блока с названием "
                                "'Висцеральный жир'.\n"
                                "Не путай висцеральный жир с процентом жира, жиром в кг, ИМТ, "
                                "безжировой массой или значениями на шкале.\n"
                                "Если точного значения нет — напиши: не найдено.\n\n"

                                "Ответ дай СТРОГО в таком формате:\n\n"

                                "⚖️ Вес: ... кг\n"
                                "🔥 Жир: ... %\n"
                                "💪 Мышечная масса: ... кг\n"
                                "💧 Вода: ... л\n"
                                "🥩 Белок: ... кг\n"
                                "🦴 Кости: ... кг\n"
                                "📉 Висцеральный жир: ...\n"
                                "🧠 BMR: ... ккал\n"
                                "🍽 Суточная норма: ... ккал\n"
                                "🎯 Оптимальный вес: ... кг\n\n"

                                "Короткий вывод Gym AI: ...\n\n"

                                "Важно: вес обязательно укажи числом, если он есть на фото."
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ]
        )

        result = response.choices[0].message.content

    except Exception as e:

        print("INBODY ERROR:", e)

        try:
            await loading_message.delete()
        except Exception:
            pass

        await message.answer(
            "⚠️ Не удалось распознать InBody.\n\n"
            "Попробуй отправить фото крупнее и четче.",
            parse_mode="HTML"
        )

        await state.clear()
        return

    try:
        await loading_message.delete()
    except Exception:
        pass

    # ==========================================
    #          ДОСТАЕМ ВЕС ИЗ ТЕКСТА
    # ==========================================

    import re

    weight_match = re.search(
        r"Вес:\s*([\d.,]+)",
        result
    )

    new_weight = None

    if weight_match:

        try:
            new_weight = float(
                weight_match.group(1).replace(",", ".")
            )
        except Exception:
            new_weight = None

    # ==========================================
    #          ОБНОВЛЯЕМ ВЕС В ПРОФИЛЕ
    # ==========================================

    if new_weight:

        profile = get_user_profile(
            message.from_user.id
        )

        if profile:

            profile["weight"] = new_weight

            save_user_profile(
                message.from_user.id,
                profile
            )

    # ==========================================
    #          СОХРАНЯЕМ INBODY
    # ==========================================

    save_inbody_result(
        message.from_user.id,
        {
            "date": str(date.today()),
            "text": result,
            "weight": new_weight
        }
    )

    # ==========================================
    #          ОТПРАВЛЯЕМ РЕЗУЛЬТАТ
    # ==========================================

    await message.answer(
        "📊 <b>Результат анализа InBody</b>\n\n"
        f"{result}\n\n"
        "✅ Данные сохранены в профиль.",

        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="👤 Профиль",
                        callback_data="menu_profile"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📸 Загрузить новый InBody",
                        callback_data="upload_inbody"
                    )
                ],
            ]
        ),

        parse_mode="HTML"
    )

    await state.clear()



# ==========================================
#            ИСТОРИЯ INBODY
# ==========================================

@router.callback_query(F.data == "inbody_history")
async def inbody_history_handler(
    callback: CallbackQuery
):

    try:
        await callback.message.delete()
    except Exception:
        pass

    history = get_inbody_history(
        callback.from_user.id
    )

    if not history:

        await callback.message.answer(
            "📈 <b>История InBody</b>\n\n"
            "У тебя пока нет сохранённых InBody.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[

                    [
                        InlineKeyboardButton(
                            text="📸 Загрузить InBody",
                            callback_data="upload_inbody"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🗑 Удалить InBody",
                            callback_data="delete_inbody"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="👤 Профиль",
                            callback_data="menu_profile"
                        )
                    ]

                ]
            ),
            parse_mode="HTML"
        )

        await callback.answer()
        return

    text = "📈 <b>История InBody</b>\n\n"

    for index, item in enumerate(
        reversed(history),
        start=1
    ):

        text += (
            f"📅 <b>{item.get('date', '-')}</b>\n"
            f"{item.get('text', '-')}\n\n"
        )

    # ==========================================
    #        ОТПРАВКА ИСТОРИИ
    # ==========================================

    await callback.message.answer(
        text[:4000],
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🗑 Удалить InBody",
                        callback_data="delete_inbody"
                   )
                ],
                [
                    InlineKeyboardButton(
                        text="📸 Загрузить новый InBody",
                        callback_data="upload_inbody"
                    )
                ],

                [
                    InlineKeyboardButton(
                        text="👤 Профиль",
                        callback_data="menu_profile"
                    )
                ]

            ]
        ),
        parse_mode="HTML"
    )

    await callback.answer()



# ==========================================
#          AI АНАЛИЗ INBODY
# ==========================================

@router.callback_query(F.data == "ai_inbody_analysis")
async def ai_inbody_analysis_handler(callback: CallbackQuery):

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
            "💎 <b>AI анализ InBody доступен в Premium</b>\n\n"
            "Premium откроет:\n"
            "• анализ динамики формы\n"
            "• сравнение InBody отчетов\n"
            "• рекомендации по жиру, мышцам и воде\n"
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
                            text="👤 Назад в профиль",
                            callback_data="menu_profile"
                        )
                    ],
                ]
            ),
            parse_mode="HTML"
        )

        await callback.answer()
        return

    # ==========================================
    #          ПОЛУЧАЕМ ИСТОРИЮ INBODY
    # ==========================================

    history = get_inbody_history(
        callback.from_user.id
    )

    if not history:

        await callback.message.answer(
            "💎 <b>AI анализ InBody</b>\n\n"
            "Пока нет данных InBody для анализа.\n\n"
            "Сначала загрузи хотя бы один отчет InBody.",
            reply_markup=profile_menu_keyboard(),
            parse_mode="HTML"
        )

        await callback.answer()
        return

    loading_message = await callback.message.answer(
        "🤖 <b>Gym AI анализирует InBody...</b>\n\n"
        "Сравниваю показатели и оцениваю динамику формы.",
        parse_mode="HTML"
    )

    try:

        response = client.responses.create(
            model="gpt-4.1-mini",
            input=(
                "Ты AI-фитнес коуч Gym AI.\n"
                "Проанализируй историю InBody пользователя на русском языке.\n\n"

                "ТВОЯ ЗАДАЧА:\n"
                "Не просто пересказать показатели, а оценить динамику формы.\n"
                "Сравни несколько последних замеров между собой.\n"
                "Особенно учитывай:\n"
                "- вес\n"
                "- процент жира\n"
                "- мышечную массу\n"
                "- воду\n"
                "- висцеральный жир\n"
                "- BMR\n\n"

                "КАК ОЦЕНИВАТЬ:\n"
                "- если вес растет, но жир снижается или мышцы растут — это хорошая динамика\n"
                "- если вес падает, но мышцы сильно снижаются — это плохая динамика\n"
                "- если жир снижается, а мышцы сохраняются — это хорошее похудение\n"
                "- если мышцы растут, а жир не растет сильно — это качественный набор\n"
                "- если вода низкая или падает — отметь это\n"
                "- если висцеральный жир растет — предупреди мягко\n"
                "- не ставь диагнозы и не делай медицинских выводов\n\n"

                "ИСТОРИЯ INBODY:\n"
                f"{history[-5:]}\n\n"

                "ФОРМАТ ОТВЕТА:\n\n"

                "💎 <b>AI анализ InBody</b>\n\n"

                "📈 <b>Динамика формы</b>\n"
                "Коротко опиши, форма улучшается, ухудшается или пока без явной динамики.\n\n"

                "✅ <b>Что улучшилось</b>\n"
                "• ...\n"
                "• ...\n\n"

                "⚠️ <b>На что обратить внимание</b>\n"
                "• ...\n"
                "• ...\n\n"

                "🎯 <b>Вывод Gym AI</b>\n"
                "Напиши общий вывод: пользователь сушится, набирает качественно, теряет мышцы, держит форму или данных пока мало.\n\n"

                "📌 <b>Рекомендации</b>\n"
                "• ...\n"
                "• ...\n"
                "• ...\n\n"

                "Если в истории только один замер, честно скажи, что полноценную динамику оценить нельзя, "
                "и дай анализ текущего состояния.\n\n"

                "Не используй Markdown. Используй только HTML <b>."
            )
        )

    except Exception as e:

        print("OPENAI INBODY ANALYSIS ERROR:", e)

        try:
            await loading_message.delete()
        except Exception:
            pass

        await callback.message.answer(
            "⚠️ <b>AI не смог проанализировать InBody</b>\n\n"
            "Попробуй ещё раз через пару секунд.",
            reply_markup=profile_menu_keyboard(),
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
        reply_markup=profile_menu_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


# ==========================================
#       КЛАВИАТУРА УДАЛЕНИЯ INBODY
# ==========================================

def delete_inbody_keyboard(history):

    buttons = []

    for index, item in enumerate(history, start=1):

        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"🗑 {index}. {item.get('date', '-')}",
                    callback_data=f"delete_inbody_{index - 1}"
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="inbody_history"
            )
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


# ==========================================
#            УДАЛЕНИЕ INBODY
# ==========================================

@router.callback_query(F.data == "delete_inbody")
async def delete_inbody_handler(callback: CallbackQuery):

    try:
        await callback.message.delete()
    except Exception:
        pass

    history = get_inbody_history(callback.from_user.id)

    if not history:

        await callback.message.answer(
            "🗑 <b>Удаление InBody</b>\n\n"
            "История InBody пустая.",
            reply_markup=profile_menu_keyboard(),
            parse_mode="HTML"
        )

        await callback.answer()
        return

    await callback.message.answer(
        "🗑 <b>Удаление InBody</b>\n\n"
        "Выбери замер, который нужно удалить:",
        reply_markup=delete_inbody_keyboard(history),
        parse_mode="HTML"
    )

    await callback.answer()


# ==========================================
#         УДАЛЕНИЕ INBODY ПО КНОПКЕ
# ==========================================

@router.callback_query(F.data.startswith("delete_inbody_"))
async def delete_inbody_by_button(callback: CallbackQuery):

    index = int(
        callback.data.replace("delete_inbody_", "")
    )

    success = delete_inbody_entry(
        callback.from_user.id,
        index
    )

    try:
        await callback.message.delete()
    except Exception:
        pass

    if success:

        await callback.answer("InBody удален")

        await inbody_history_handler(callback)

    else:

        await callback.message.answer(
            "❌ Не удалось удалить InBody.",
            reply_markup=profile_menu_keyboard(),
            parse_mode="HTML"
        )

        await callback.answer()