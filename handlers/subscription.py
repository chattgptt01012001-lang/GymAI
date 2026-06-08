# ==========================================
#               ИМПОРТЫ
# ==========================================

from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from storage import (
    get_premium_status,
    get_premium_until,
)

from datetime import datetime

from config import PREMIUM_PRICE
from robokassa import create_premium_payment_link

# ==========================================
#               ROUTER
# ==========================================

router = Router()

# ==========================================
#              PREMIUM ТАРИФЫ
# ==========================================

PREMIUM_PLANS = {
    "week": {
        "title": "🔥 Неделя",
        "days": 7,
        "price": "149.00",
        "button": "🔥 Неделя • 149 ₽",
    },
    "month": {
        "title": "💪 Месяц",
        "days": 30,
        "price": "499.00",
        "button": "💪 Месяц • 499 ₽",
    },
    "three_months": {
        "title": "🚀 3 месяца",
        "days": 90,
        "price": "1190.00",
        "button": "🚀 3 месяца • 1190 ₽",
    },
}


# ==========================================
#        КЛАВИАТУРА PREMIUM
# ==========================================

def premium_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔥 Неделя • 149 ₽",
                    callback_data="buy_premium_week"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💪 Месяц • 499 ₽",
                    callback_data="buy_premium_month"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🚀 3 месяца • 1190 ₽",
                    callback_data="buy_premium_three_months"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Что входит",
                    callback_data="premium_features"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data="back_to_main_menu"
                )
            ],
        ]
    )


# ==========================================
#              PREMIUM МЕНЮ
# ==========================================

@router.callback_query(F.data == "subscription")
async def premium_handler(callback: CallbackQuery):

    try:
        await callback.message.delete()
    except Exception:
        pass

    # ==========================================
    #          ПРОВЕРЯЕМ PREMIUM СТАТУС
    # ==========================================

    is_premium = get_premium_status(
        callback.from_user.id
    )

    if is_premium:

        status_text = (
        "🟢 <b>Premium активен</b>\n"
        "Все функции Gym AI доступны."
    )

        button_text = "✅ Premium уже активен"

    else:

        status_text = (
        "⚪ <b>Бесплатный тариф</b>\n"
        "Доступны только базовые функции."
    )

        button_text = "🚀 Активировать Premium"

    # ==========================================
    #          КЛАВИАТУРА PREMIUM
    # ==========================================

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=button_text,
                    callback_data="buy_premium"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Что входит",
                    callback_data="premium_features"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data="back_to_main_menu"
                )
            ],
        ]
    )

    # ==========================================
    #          ОТПРАВКА PREMIUM МЕНЮ
    # ==========================================

    await callback.message.answer(
    "💎 <b>GYM AI PREMIUM</b>\n\n"

    "Открой все возможности персонального AI-тренера.\n\n"

    "🔥 <b>Что станет доступно:</b>\n\n"

    "🧠 Продвинутый AI план тренировок\n"
    "📊 AI анализ тренировок\n"
    "📈 AI анализ прогресса\n"
    "😴 AI рекомендации по восстановлению\n"
    "🔥 Персональная мотивация\n"
    "🍱 Меню питания на день\n"
    "📔 Дневник питания\n"
    "🤖 AI анализ питания\n"
    "📊 Расширенный анализ InBody\n"
    "🤖 Безлимитный AI Коуч\n\n"

    "━━━━━━━━━━━━━━\n\n"

    "📌 <b>Текущий статус:</b>\n"
    f"{status_text}\n\n",
    reply_markup=keyboard,
    parse_mode="HTML"
)

    await callback.answer()


# ==========================================
#              ЧТО ВХОДИТ
# ==========================================

@router.callback_query(F.data == "premium_features")
async def premium_features_handler(callback: CallbackQuery):

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        "📋 <b>ЧТО ВХОДИТ В GYM AI PREMIUM</b>\n\n"

        "Premium открывает все сильные функции бота без ограничений.\n\n"

        "━━━━━━━━━━━━━━\n\n"

        "🏋️ <b>Тренировки</b>\n\n"
        "🧠 Продвинутый AI план тренировок\n"
        "📊 AI анализ тренировок\n"
        "📈 Анализ прогресса\n"
        "😴 Рекомендации по восстановлению\n"
        "🔥 Персональная мотивация\n\n"

        "🍽 <b>Питание</b>\n\n"
        "🍱 Меню питания на день\n"
        "📔 Дневник питания\n"
        "💧 Учет воды\n"
        "🤖 AI анализ питания\n\n"

        "🤖 <b>AI Коуч</b>\n\n"
        "♾️ Безлимитные вопросы\n"
        "🏋️ Советы по тренировкам\n"
        "🍽 Советы по питанию\n"
        "📈 Анализ прогресса\n\n"

        "📊 <b>Аналитика тела</b>\n\n"
        "🧠 AI анализ InBody\n"
        "📈 Оценка динамики формы\n"
        "💪 Рекомендации по мышцам, жиру и воде\n\n"

        "━━━━━━━━━━━━━━\n\n"

        "💎 Premium превращает Gym AI в персонального фитнес-ассистента.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🚀 Активировать Premium",
                callback_data="buy_premium"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад в Premium",
                callback_data="subscription"
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
#           ПОКУПКА PREMIUM
# ==========================================

@router.callback_query(F.data == "buy_premium")
async def buy_premium_handler(callback: CallbackQuery):

    try:
        await callback.message.delete()
    except Exception:
        pass

    user_id = callback.from_user.id

    inv_id = int(
        datetime.now().timestamp()
    )

    payment_link = create_premium_payment_link(
        user_id=user_id,
        inv_id=inv_id,
        amount=PREMIUM_PRICE,
        description="Gym AI Premium"
    )

    await callback.message.answer(
        "💎 <b>Оформление Premium</b>\n\n"
        "Нажми кнопку ниже, чтобы перейти к оплате.\n\n"
        f"Стоимость: <b>{PREMIUM_PRICE} ₽</b>\n\n"
        "После успешной оплаты Premium будет активирован автоматически.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💳 Оплатить Premium",
                        url=payment_link
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ Назад",
                        callback_data="subscription"
                    )
                ],
            ]
        ),
        parse_mode="HTML"
    )

    await callback.answer()