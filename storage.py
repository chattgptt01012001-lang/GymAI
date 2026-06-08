# ==========================================
#               ИМПОРТЫ
# ==========================================

import json
import os

from datetime import datetime, timedelta


# ==========================================
#              ФАЙЛ БАЗЫ
# ==========================================

USERS_FILE = "users.json"


# ==========================================
#          ЗАГРУЗКА ПОЛЬЗОВАТЕЛЕЙ
# ==========================================

def load_users():

    if not os.path.exists(USERS_FILE):
        return {}

    with open(USERS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


# ==========================================
#         СОХРАНЕНИЕ ПОЛЬЗОВАТЕЛЕЙ
# ==========================================

def save_users(users):

    with open(USERS_FILE, "w", encoding="utf-8") as file:
        json.dump(users, file, ensure_ascii=False, indent=4)


# ==========================================
#      ПРОВЕРКА: ПОЛЬЗОВАТЕЛЬ ЕСТЬ?
# ==========================================

def is_user_registered(user_id):

    users = load_users()

    return str(user_id) in users


# ==========================================
#       РЕГИСТРАЦИЯ ПОЛЬЗОВАТЕЛЯ
# ==========================================

def register_user(user_id, data=None):

    users = load_users()
    user_id = str(user_id)

    if user_id not in users:
        users[user_id] = {}

    users[user_id]["registered"] = True

    if data:
        users[user_id].update(data)

    save_users(users)


# ==========================================
#             СОХРАНЕНИЕ КБЖУ
# ==========================================

def save_user_kbju(user_id, kbju):

    users = load_users()
    user_id = str(user_id)

    if user_id not in users:
        users[user_id] = {
            "registered": True
        }

    users[user_id]["kbju"] = kbju

    save_users(users)


# ==========================================
#             ПОЛУЧЕНИЕ КБЖУ
# ==========================================

def get_user_kbju(user_id):

    users = load_users()
    user_id = str(user_id)

    if user_id not in users:
        return None

    return users[user_id].get("kbju")   


# ==========================================
#          СОХРАНЕНИЕ ПРОФИЛЯ
# ==========================================

def save_user_profile(user_id, profile_data):

    users = load_users()
    user_id = str(user_id)

    if user_id not in users:
        users[user_id] = {
            "registered": True
        }

    users[user_id]["profile"] = profile_data

    save_users(users)


# ==========================================
#          ПОЛУЧЕНИЕ ПРОФИЛЯ
# ==========================================

def get_user_profile(user_id):

    users = load_users()
    user_id = str(user_id)

    if user_id not in users:
        return None

    return users[user_id].get("profile")


# ==========================================
#          ДОБАВЛЕНИЕ БЛЮДА В ДНЕВНИК
# ==========================================

def add_food_diary_entry(user_id, meal_data):

    users = load_users()
    user_id = str(user_id)

    if user_id not in users:
        users[user_id] = {
            "registered": True
        }

    if "food_diary" not in users[user_id]:
        users[user_id]["food_diary"] = []

    users[user_id]["food_diary"].append(meal_data)

    save_users(users)


# ==========================================
#          ПОЛУЧЕНИЕ ДНЕВНИКА ПИТАНИЯ
# ==========================================

def get_food_diary(user_id):

    users = load_users()
    user_id = str(user_id)

    if user_id not in users:
        return []

    return users[user_id].get("food_diary", [])


# ==========================================
#        УДАЛЕНИЕ БЛЮДА ИЗ ДНЕВНИКА
# ==========================================

def delete_food_diary_entry(user_id, index):

    users = load_users()

    user_id = str(user_id)

    if user_id not in users:
        return False

    diary = users[user_id].get("food_diary", [])

    if index < 0 or index >= len(diary):
        return False

    diary.pop(index)

    users[user_id]["food_diary"] = diary

    save_users(users)

    return True

# ==========================================
#              СОХРАНЕНИЕ ВОДЫ
# ==========================================

def add_water_entry(user_id, amount_ml, current_date):

    users = load_users()
    user_id = str(user_id)

    if user_id not in users:
        users[user_id] = {"registered": True}

    water_data = users[user_id].get("water", {})

    if isinstance(water_data, int):
        water_data = {
            current_date: water_data
        }

    if current_date not in water_data:
        water_data[current_date] = 0

    water_data[current_date] += amount_ml

    users[user_id]["water"] = water_data

    save_users(users)


# ==========================================
#              ПОЛУЧЕНИЕ ВОДЫ
# ==========================================

def get_water_amount(user_id, current_date):

    users = load_users()
    user_id = str(user_id)

    if user_id not in users:
        return 0

    water_data = users[user_id].get("water", {})

    if isinstance(water_data, int):
        return water_data

    return water_data.get(current_date, 0)


# ==========================================
#              УДАЛЕНИЕ ВОДЫ
# ==========================================

def remove_water_entry(user_id, amount_ml, current_date):

    users = load_users()

    user_id = str(user_id)

    if user_id not in users:
        return

    water_data = users[user_id].get("water", {})

    if isinstance(water_data, int):

        water_data = {
            current_date: water_data
        }

    if current_date not in water_data:
        water_data[current_date] = 0

    water_data[current_date] -= amount_ml

    if water_data[current_date] < 0:
        water_data[current_date] = 0

    users[user_id]["water"] = water_data

    save_users(users)


# ==========================================
#          СОХРАНЕНИЕ ПЛАНА ТРЕНИРОВОК
# ==========================================

def save_workout_plan(user_id, plan_data):

    users = load_users()
    user_id = str(user_id)

    if user_id not in users:
        users[user_id] = {
            "registered": True
        }

    users[user_id]["workout_plan"] = plan_data

    save_users(users)


# ==========================================
#          ПОЛУЧЕНИЕ ПЛАНА ТРЕНИРОВОК
# ==========================================

def get_workout_plan(user_id):

    users = load_users()
    user_id = str(user_id)

    if user_id not in users:
        return None

    return users[user_id].get("workout_plan")


# ==========================================
#          УДАЛЕНИЕ ПЛАНА ТРЕНИРОВОК
# ==========================================

def delete_workout_plan(user_id):

    users = load_users()
    user_id = str(user_id)

    if user_id not in users:
        return False

    if "workout_plan" not in users[user_id]:
        return False

    del users[user_id]["workout_plan"]

    save_users(users)

    return True


# ==========================================
#          ДОБАВЛЕНИЕ ТРЕНИРОВКИ В ИСТОРИЮ
# ==========================================

def add_workout_history_entry(user_id, workout_data):

    users = load_users()
    user_id = str(user_id)

    if user_id not in users:
        users[user_id] = {"registered": True}

    if "workout_history" not in users[user_id]:
        users[user_id]["workout_history"] = []

    users[user_id]["workout_history"].append(workout_data)

    save_users(users)


# ==========================================
#          ПОЛУЧЕНИЕ ИСТОРИИ ТРЕНИРОВОК
# ==========================================

def get_workout_history(user_id):

    users = load_users()
    user_id = str(user_id)

    if user_id not in users:
        return []

    return users[user_id].get("workout_history", [])


# ==========================================
#       УДАЛЕНИЕ ТРЕНИРОВКИ ИЗ ИСТОРИИ
# ==========================================

def delete_workout_history_entry(user_id, index):

    users = load_users()
    user_id = str(user_id)

    if user_id not in users:
        return False

    history = users[user_id].get("workout_history", [])

    if index < 0 or index >= len(history):
        return False

    history.pop(index)

    users[user_id]["workout_history"] = history

    save_users(users)

    return True



# ==========================================
#            СОХРАНЕНИЕ INBODY
# ==========================================

def save_inbody_result(user_id, inbody_data):

    users = load_users()

    user_id = str(user_id)

    if user_id not in users:
        users[user_id] = {
            "registered": True
        }

    if "inbody_history" not in users[user_id]:
        users[user_id]["inbody_history"] = []

    users[user_id]["inbody_history"].append(inbody_data)

    users[user_id]["last_inbody"] = inbody_data

    save_users(users)


# ==========================================
#            ПОЛУЧЕНИЕ INBODY
# ==========================================

def get_inbody_result(user_id):

    users = load_users()

    user_id = str(user_id)

    if user_id not in users:
        return None

    return users[user_id].get("last_inbody")


# ==========================================
#          ИСТОРИЯ INBODY
# ==========================================

def get_inbody_history(user_id):

    users = load_users()

    user_id = str(user_id)

    if user_id not in users:
        return []

    return users[user_id].get("inbody_history", [])


# ==========================================
#            УДАЛЕНИЕ INBODY
# ==========================================

def delete_inbody_entry(user_id, index):

    users = load_users()
    user_id = str(user_id)

    if user_id not in users:
        return False

    history = users[user_id].get("inbody_history", [])

    if index < 0 or index >= len(history):
        return False

    history.pop(index)

    users[user_id]["inbody_history"] = history

    if history:
        users[user_id]["last_inbody"] = history[-1]
    else:
        users[user_id].pop("last_inbody", None)

    save_users(users)

    return True


# ==========================================
#          PREMIUM СТАТУС
# ==========================================

def activate_premium(user_id, days):

    users = load_users()
    user_id = str(user_id)

    if user_id not in users:
        users[user_id] = {
            "registered": True
        }

    current_until = users[user_id].get("premium_until")

    if current_until:

        try:
            current_date = datetime.strptime(
                current_until,
                "%Y-%m-%d"
            )

            if current_date > datetime.now():
                start_date = current_date
            else:
                start_date = datetime.now()

        except Exception:
            start_date = datetime.now()

    else:
        start_date = datetime.now()

    premium_until = (
        start_date + timedelta(days=days)
    ).strftime("%Y-%m-%d")

    users[user_id]["premium_until"] = premium_until
    users[user_id]["premium"] = True

    save_users(users)

    return premium_until


def deactivate_premium(user_id):

    users = load_users()
    user_id = str(user_id)

    if user_id not in users:
        return False

    users[user_id]["premium"] = False
    users[user_id].pop("premium_until", None)

    save_users(users)

    return True


def set_premium_status(user_id, status):

    if status:
        return activate_premium(user_id, 30)

    return deactivate_premium(user_id)


def get_premium_status(user_id):

    users = load_users()
    user_id = str(user_id)

    if user_id not in users:
        return False

    premium_until = users[user_id].get("premium_until")

    if not premium_until:
        return users[user_id].get("premium", False)

    try:
        premium_date = datetime.strptime(
            premium_until,
            "%Y-%m-%d"
        )

        if premium_date >= datetime.now():
            return True

        users[user_id]["premium"] = False
        save_users(users)

        return False

    except Exception:
        return False


def get_premium_until(user_id):

    users = load_users()
    user_id = str(user_id)

    if user_id not in users:
        return None

    return users[user_id].get("premium_until")

# ==========================================
#       ЛИМИТ ВОПРОСОВ AI КОУЧА
# ==========================================

def get_ai_coach_usage(user_id, today):

    users = load_users()
    user_id = str(user_id)

    if user_id not in users:
        return 0

    if users[user_id].get("coach_requests_date") != today:
        return 0

    return users[user_id].get("coach_requests_today", 0)


def increment_ai_coach_usage(user_id, today):

    users = load_users()
    user_id = str(user_id)

    if user_id not in users:
        users[user_id] = {
            "registered": True
        }

    if users[user_id].get("coach_requests_date") != today:
        users[user_id]["coach_requests_date"] = today
        users[user_id]["coach_requests_today"] = 0

    users[user_id]["coach_requests_today"] += 1

    save_users(users)