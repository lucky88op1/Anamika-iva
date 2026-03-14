import asyncio
import websockets
import json
import requests
import re
import time
from datetime import datetime
import phonenumbers
from phonenumbers import geocoder

BOT_TOKEN = "8161605259:AAF--gXMcuiH4EySJij5f_UhT5oNZ-h--Qc"
CHAT_ID = "-1002938168131"

WS_URL = "wss://ivas.tempnum.qzz.io:2087/socket.io/?EIO=4&transport=websocket"
sent_otps = set()


def extract_otp(msg):

    m = re.search(r"\d{3}-\d{3}", msg)
    if m:
        return m.group()

    m = re.search(r"\d{4,6}", msg)
    if m:
        return m.group()

    return None


def mask_number(num):

    num = re.sub(r"\D", "", num)

    if len(num) < 6:
        return num

    return f"{num[:3]}XXXX{num[-3:]}"


def detect_service(msg):

    m = msg.lower()

    if "whatsapp" in m:
        return "🟢 WhatsApp"

    if "telegram" in m:
        return "✈️ Telegram"

    if "facebook" in m:
        return "📘 Facebook"

    if "google" in m:
        return "🔴 Google"

    if "instagram" in m:
        return "📷 Instagram"

    return "📩 OTP"


def get_country(number):

    try:
        num = phonenumbers.parse("+" + number)
        country = geocoder.description_for_number(num, "en")
        region = phonenumbers.region_code_for_number(num)
        flag = "".join(chr(127397 + ord(c)) for c in region)
        return country, flag
    except:
        return "Unknown", "🌍"


def send_message(country, flag, service, number, otp, fullmsg):

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    text = f"""
<b>{flag} New {country} {service} OTP !</b>

<blockquote>
⏰ Time: {now}

🌍 Country: {country}

📲 Service: {service}

📞 Number: {number}

🔑 OTP: <code>{otp}</code>
</blockquote>

📩 <b>Full Message:</b>

<blockquote>{fullmsg}</blockquote>

━━━━━━━━━━━━━━
<b>Powered By LUCKY 👑</b>
"""

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [
                [
                    {"text": "🏛 Number", "url": "https://t.me/NumOTPV2BOT"},
                    {"text": "👾 Developer", "url": "https://t.me/ngxgod1"}
                ],
                [
                    {"text": "📢 Channel", "url": "https://t.me/TeamOFDark1"},
                    {"text": "🟢 OTP", "url": "https://t.me/forwardforme1"}
                ]
            ]
        }
    }

    requests.post(url, json=payload)


async def ping(ws, interval):

    while True:
        await asyncio.sleep(interval / 1000)
        try:
            await ws.send("3")
        except:
            break


async def start():

    while True:

        try:

            async with websockets.connect(WS_URL, ping_interval=None) as ws:

                print("✅ Connected IVAS")

                msg = await ws.recv()

                interval = 25000

                if msg.startswith("0{"):
                    data = json.loads(msg[1:])
                    interval = data.get("pingInterval", 25000)

                await ws.send("40/livesms,")

                asyncio.create_task(ping(ws, interval))

                while True:

                    data = await ws.recv()

                    if data.startswith("42/livesms,"):

                        payload = json.loads(data[data.find("["):])

                        sms = payload[1]

                        message = sms.get("message", "")
                        number = sms.get("recipient", "")

                        otp = extract_otp(message)

                        if not otp:
                            continue

                        if otp in sent_otps:
                            continue

                        sent_otps.add(otp)

                        service = detect_service(message)

                        country, flag = get_country(number)

                        masked = mask_number(number)

                        send_message(
                            country,
                            flag,
                            service,
                            masked,
                            otp,
                            message
                        )

                        print("OTP SENT")

        except Exception as e:

            print("Reconnecting...", e)

            time.sleep(5)


asyncio.run(start())
