import os
import requests
from bs4 import BeautifulSoup

LINK_CALENDAR = "https://calendar.app.google/URnpmiyiKZtAurqP8"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

def enviar_telegram(mensaje):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Error: Faltan las variables de entorno de Telegram.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"❌ Error al enviar mensaje a Telegram: {e}")

def verificar_turnos():
    try:
        session = requests.Session()
        res = session.get(LINK_CALENDAR, headers=HEADERS, timeout=15, allow_redirects=True)
        html = res.text

        sin_turnos = (
            "No hay horarios disponibles" in html or 
            "No available times" in html or 
            "No slots" in html
        )

        if not sin_turnos and res.status_code == 200:
            msg = (
                f"<b>¡TURNO DETECTADO EN GOOGLE CALENDAR!</b>\n\n"
                f"Parece que se liberó un espacio en la agenda.\n\n"
                f"Reservá rápido acá: {LINK_CALENDAR}"
            )
            print("🚀 ¡Turno detectado! Enviando alerta...")
            enviar_telegram(msg)
        else:
            print("🔍 Chequeo realizado: Aún no hay turnos disponibles.")

    except Exception as e:
        print(f"❌ Error al verificar la agenda: {e}")

if __name__ == "__main__":
    verificar_turnos()