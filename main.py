import requests
import time
import telebot
from telebot import types
from datetime import datetime
import pytz
import threading

TOKEN = '7957207504:AAGEKxZrEcAI1iLgdKw6bvrLQ9rylYuqK_I'
bot = telebot.TeleBot(TOKEN)

API_URL = "https://api.alerts.in.ua/v1/alerts/active.json"
API_TOKEN = "3b5106a1058f3c29227de73d95c1dcabc2488358ab2203"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Cache-Control": "no-cache"
}




REGIONS = [
    "Вінницька область", "Волинська область", "Дніпропетровська область", "Донецька область",
    "Житомирська область", "Закарпатська область", "Запорізька область", "Івано-Франківська область",
    "Київська область", "Кіровоградська область", "Луганська область", "Львівська область",
    "Миколаївська область", "Одеська область", "Полтавська область", "Рівненська область",
    "Сумська область", "Тернопільська область", "Харківська область", "Херсонська область",
    "Хмельницька область", "Черкаська область", "Чернівецька область", "Чернігівська область", "Автономна Республіка Крим",
    "м. Київ"
]


active_monitoring_threads = {}
alerts_status = {}


def get_active_alerts():
    response = requests.get(API_URL, headers=headers)
    if response.status_code == 200:
        return response.json().get("alerts", [])
    return []


def check_current_alert_status(region):
    kyiv_tz = pytz.timezone("Europe/Kyiv")
    alerts = get_active_alerts()

    oblast_alerts = [
        alert for alert in alerts
        if alert.get("location_oblast") == region and alert.get("location_title", "").strip() == region
    ]

    if oblast_alerts:
        start_time = oblast_alerts[0].get("started_at", "невідомо")
        if start_time != "невідомо":
            start_time = pytz.utc.localize(datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%fZ")).astimezone(kyiv_tz)
            start_time = start_time.strftime("%d/%m/%Y %H:%M:%S")
        return True, f"🚨 {region}: активна тривога! Початок: {start_time}."
    else:
        return False, f"✅ {region}: тривога не активна."


def check_region_alerts(monitoring_state, stop_event):
    region = monitoring_state["region"]
    chat_id = monitoring_state["chat_id"]

    while not stop_event.is_set():
        current_alert_status, message = check_current_alert_status(region)

        last_status = alerts_status.get(region, None)

        if current_alert_status != last_status:
            bot.send_message(chat_id, message)
            alerts_status[region] = current_alert_status

        time.sleep(10)


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
    bot.send_message(chat_id, f"🔍 {region}: Моніторинг тривог розпочато.")

    stop_event = threading.Event()
    monitoring_thread = threading.Thread(
        target=check_region_alerts, args=(monitoring_state, stop_event), daemon=True
    )
    monitoring_thread.start()

    active_monitoring_threads[chat_id] = (stop_event, monitoring_thread)


if __name__ == "__main__":
    print("Бот запущено...")
    bot.polling(non_stop=True)
