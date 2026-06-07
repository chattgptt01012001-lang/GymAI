# ==========================================
#               ИМПОРТЫ
# ==========================================

from dotenv import load_dotenv
import os


# ==========================================
#          ЗАГРУЗКА .env
# ==========================================

load_dotenv()


# ==========================================
#            TELEGRAM TOKEN
# ==========================================

BOT_TOKEN = os.getenv("BOT_TOKEN")


# ==========================================
#             OPENAI TOKEN
# ==========================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ==========================================
#               АДМИНКА
# ==========================================

ADMIN_IDS = [
    465811509
]

# ==========================================
#             ОПЛАТА ПОДПИСКИ
# ==========================================

ROBOKASSA_MERCHANT_LOGIN = os.getenv("ROBOKASSA_MERCHANT_LOGIN")
ROBOKASSA_PASSWORD_1 = os.getenv("ROBOKASSA_PASSWORD_1")
ROBOKASSA_PASSWORD_2 = os.getenv("ROBOKASSA_PASSWORD_2")

ROBOKASSA_TEST_MODE = True

PREMIUM_PRICE = "299.00"