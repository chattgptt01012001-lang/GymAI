# ==========================================
#             ROBOKASSA HELPERS
# ==========================================

import hashlib
from urllib.parse import urlencode

from config import (
    ROBOKASSA_MERCHANT_LOGIN,
    ROBOKASSA_PASSWORD_1,
    ROBOKASSA_TEST_MODE,
)


ROBOKASSA_PAYMENT_URL = "https://auth.robokassa.ru/Merchant/Index.aspx"


# ==========================================
#          СОЗДАНИЕ ПОДПИСИ ОПЛАТЫ
# ==========================================

def create_payment_signature(
    merchant_login,
    out_sum,
    inv_id,
    password_1,
    user_id
):

    signature_string = (
        f"{merchant_login}:"
        f"{out_sum}:"
        f"{inv_id}:"
        f"{password_1}:"
        f"Shp_user_id={user_id}"
    )

    return hashlib.md5(
        signature_string.encode("utf-8")
    ).hexdigest()


# ==========================================
#          СОЗДАНИЕ ССЫЛКИ НА ОПЛАТУ
# ==========================================

def create_premium_payment_link(
    user_id,
    inv_id,
    amount,
    description
):

    signature = create_payment_signature(
        merchant_login=ROBOKASSA_MERCHANT_LOGIN,
        out_sum=amount,
        inv_id=inv_id,
        password_1=ROBOKASSA_PASSWORD_1,
        user_id=user_id
    )

    params = {
        "MerchantLogin": ROBOKASSA_MERCHANT_LOGIN,
        "OutSum": amount,
        "InvId": inv_id,
        "Description": description,
        "SignatureValue": signature,
        "Shp_user_id": user_id,
        "Culture": "ru",
    }

    if ROBOKASSA_TEST_MODE:
        params["IsTest"] = 1

    return (
        ROBOKASSA_PAYMENT_URL
        + "?"
        + urlencode(params)
    )