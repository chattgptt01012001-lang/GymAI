# ==========================================
#               ИМПОРТЫ
# ==========================================

import asyncio

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN

# START SCREEN
from handlers.start import router as start_router

# АНКЕТА + КБЖУ
from handlers.profile import router as profile_router

# MENU
from handlers.menu import router as menu_router

# FOOD
from handlers.food import router as food_router

# PROFILE BLOCK
from handlers.profile_block import router as profile_block_router

# БЛОК ТРЕНИРОВОК 
from handlers.workout import router as workout_router

# AI КОУЧ
from handlers.ai_coach import router as ai_coach_router

# PREMIUM
from handlers.subscription import router as subscription_router

# ADMIN
from handlers.admin import router as admin_router


# ==========================================
#            ГЛАВНАЯ ФУНКЦИЯ
# ==========================================

async def main():

    # СОЗДАЕМ БОТА
    bot = Bot(token=BOT_TOKEN)

    # СОЗДАЕМ DISPATCHER
    dp = Dispatcher()

    # START
    dp.include_router(start_router)

    # PROFILE
    dp.include_router(profile_router)

    # PROFILE BLOCK
    dp.include_router(profile_block_router)

    # MENU
    dp.include_router(menu_router)

    # FOOD
    dp.include_router(food_router)

    # WORKOUT
    dp.include_router(workout_router)
    
    # AI КОУЧ
    dp.include_router(ai_coach_router)

    # PREMIUM
    dp.include_router(subscription_router)

    # ADMIN
    dp.include_router(admin_router)

    print("Gym AI запущен 🚀")

    await dp.start_polling(bot)


# ==========================================
#              ЗАПУСК БОТА
# ==========================================

if __name__ == "__main__":
    asyncio.run(main())