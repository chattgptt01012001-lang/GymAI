# ==========================================
#          ROBOKASSA WEBHOOK
# ==========================================

import hashlib

from aiohttp import web

from config import ROBOKASSA_PASSWORD_2
from storage import set_premium_status


def check_result_signature(out_sum, inv_id, signature, user_id):

    sign_string = (
        f"{out_sum}:"
        f"{inv_id}:"
        f"{ROBOKASSA_PASSWORD_2}:"
        f"Shp_user_id={user_id}"
    )

    correct_signature = hashlib.md5(
        sign_string.encode("utf-8")
    ).hexdigest()

    return correct_signature.lower() == signature.lower()


async def robokassa_result_handler(request):

    data = await request.post()

    out_sum = data.get("OutSum")
    inv_id = data.get("InvId")
    signature = data.get("SignatureValue")
    user_id = data.get("Shp_user_id")

    if not all([out_sum, inv_id, signature, user_id]):
        return web.Response(text="bad request", status=400)

    if not check_result_signature(
        out_sum,
        inv_id,
        signature,
        user_id
    ):
        return web.Response(text="bad sign", status=403)

    set_premium_status(
        user_id,
        True
    )

    return web.Response(
        text=f"OK{inv_id}"
    )


def create_web_app():

    app = web.Application()

    app.router.add_post(
        "/robokassa/result",
        robokassa_result_handler
    )

    return app