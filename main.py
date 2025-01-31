import os
import requests
import time
import telebot
from telebot import types
from datetime import datetime
import pytz
import threading
from flask import Flask

TOKEN = '7957207504:AAGEKxZrEcAI1iLgdKw6bvrLQ9rylYuqK_I'
bot = telebot.TeleBot(TOKEN)

API_URL = "https://api.alerts.in.ua/v1/alerts/active.json"
API_TOKEN = "3b5106a1058f3c29227de73d95c1dcabc2488358ab2203"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Cache-Control": "no-cache"
}

app = Flask(__name__)

REGIONS = [
    "Автономна Республіка Крим", "Вінницька область", "Волинська область", "Дніпропетровська область", "Донецька область",
    "Житомирська область", "Закарпатська область", "Запорізька область", "Івано-Франківська область",
    "Київська область", "Кіровоградська область", "Луганська область", "Львівська область",
    "Миколаївська область", "Одеська область", "Полтавська область", "Рівненська область",
    "Сумська область", "Тернопільська область", "Харківська область", "Херсонська область",
    "Хмельницька область", "Черкаська область", "Чернівецька область", "Чернігівська область", "м. Київ"
]

active_monitoring_threads = {}


def get_active_alerts():
    response = requests.get(API_URL, headers=headers)
    if response.status_code == 200:
        return response.json().get("alerts", [])
    return []


def check_current_alert_status(region):
    kyiv_tz = pytz.timezone("Europe/Kyiv")
    alerts = get_active_alerts()

    oblast_wide_alerts = [
        alert for alert in alerts
        if alert.get("location_oblast") == region and alert.get("location_title", "").strip() == region
    ]

    if not oblast_wide_alerts:
        filtered_alerts = [
            alert for alert in alerts
            if alert.get("location_oblast") == region and "район" not in alert.get("location_title", "").lower()
        ]
    else:
        filtered_alerts = oblast_wide_alerts

    if filtered_alerts:
        start_time = filtered_alerts[0].get("started_at", "невідомо")
        if start_time != 'невідомо':
            start_time = pytz.utc.localize(datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%fZ")).astimezone(kyiv_tz)
            start_time = start_time.strftime("%d/%m/%Y %H:%M:%S")
        return True, f"🚨 {region}: активна тривога! Початок: {start_time}."
    else:
        return False, f"✅ {region}: повітряна тривога не активна."


def check_region_alerts(monitoring_state, last_alert_status, stop_event):
    while not stop_event.is_set():
        region = monitoring_state["region"]
        chat_id = monitoring_state["chat_id"]

        current_alert_status, message = check_current_alert_status(region)

        if current_alert_status != last_alert_status[0]:
            bot.send_message(chat_id, message)
            last_alert_status[0] = current_alert_status

        time.sleep(15)


@bot.message_handler(commands=["start"])
def set_monitored_region(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for region in REGIONS:
        keyboard.add(types.KeyboardButton(region))
    bot.send_message(message.chat.id, "Оберіть область для моніторингу:", reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.text in REGIONS)
def start_monitoring(message):
    region = message.text
    chat_id = message.chat.id

    if chat_id in active_monitoring_threads:
        stop_event, thread = active_monitoring_threads[chat_id]
        stop_event.set()
        thread.join()

    monitoring_state = {"region": region, "chat_id": chat_id}
    current_alert_status, initial_message = check_current_alert_status(region)
    bot.send_message(chat_id, f"🔍 {region}: Моніторинг тривог розпочато.")
    bot.send_message(chat_id, initial_message)

    last_alert_status = [current_alert_status]
    stop_event = threading.Event()

    monitoring_thread = threading.Thread(
        target=check_region_alerts, args=(monitoring_state, last_alert_status, stop_event), daemon=True
    )
    monitoring_thread.start()

    active_monitoring_threads[chat_id] = (stop_event, monitoring_thread)


if __name__ == "__main__":
    # Запускаємо bot.polling у фоновому потоці
    threading.Thread(target=lambda: bot.polling(non_stop=True), daemon=True).start()

    # Запуск Flask-сервера на вказаному порту
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
