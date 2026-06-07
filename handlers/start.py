# ==========================================
#               ИМПОРТЫ
# ==========================================

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile,
)

from keyboards.main_menu import main_menu_keyboard
from storage import (
    is_user_registered,
    get_user_profile,
)

from keyboards.main_menu import (
    main_menu_keyboard,
    get_main_menu_text
)

# ==========================================
#            СОЗДАНИЕ ROUTER
# ==========================================

router = Router()


# ==========================================
#          КОМАНДА /start
# ==========================================

@router.message(CommandStart())
async def start_handler(message: Message):
    
    print("START HANDLER WORKED", flush=True)

    if is_user_registered(message.from_user.id):

        await message.answer(
            get_main_menu_text(
                message.from_user.id
            ),
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )

        return

    # ==========================================
    #       ЕСЛИ ПОЛЬЗОВАТЕЛЬ НОВЫЙ
    # ==========================================

    photo = FSInputFile(
        "assets/welcome.png"
    )

    await message.answer_photo(
        photo=photo,
        caption=(
            "✌🏻 <b>Привет! Я Gym AI</b>\n\n"

            "Твой личный AI-помощник "
            "по питанию и тренировкам.\n\n"

            "<b>Перед стартом важно:</b>\n\n"

            "• Я — AI-помощник, а не медицинский специалист.\n"
            "• При наличии заболеваний и ограничений "
            "по здоровью проконсультируйся с врачом.\n"
            "• Мои рекомендации носят информационный характер.\n"
            "• Для персонализации я собираю данные:\n"
            "пол, возраст, вес и рост.\n\n"

            "Чтобы посчитать норму калорий и БЖУ, "
            "мне нужно задать тебе несколько вопросов 👇"
        ),

        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔥 Погнали",
                        callback_data="start_onboarding"
                    )
                ]
            ]
        ),

        parse_mode="HTML"
    )


# ==========================================
#          DEBUG: ЛЮБОЕ СООБЩЕНИЕ
# ==========================================

@router.message()
async def debug_any_message(message: Message):

    print(
        f"DEBUG MESSAGE: {message.from_user.id} | {message.text}",
        flush=True
    )

    await message.answer(
        f"DEBUG получил сообщение: {message.text}"
    )