import os
import requests
from bs4 import BeautifulSoup
from http.server import BaseHTTPRequestHandler

# Link de Google Calendar
LINK_CALENDAR = "https://calendar.app.google/URnpmiyiKZtAurqP8"

TELEGRAM_TOKEN = os.getenv("8932905331:AAG6mOmCoPVjqvWWD0YpBRAZfi0Wm0jLf-E")
TELEGRAM_CHAT_ID = os.getenv("5892894506")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

def enviar_telegram(mensaje):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Faltan configurar las variables de entorno de Telegram.")
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
        print(f"Error al enviar mensaje a Telegram: {e}")

def verificar_turnos():
    try:
        session = requests.Session()
        res = session.get(LINK_CALENDAR, headers=HEADERS, timeout=15, allow_redirects=True)
        html = res.text

        # Búsqueda de señales de falta de turnos en el HTML renderizado por Google
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
            enviar_telegram(msg)
            return "¡Turno detectado y notificación enviada!"
        else:
            return "Chequeo finalizado: Aún no hay turnos disponibles."

    except Exception as e:
        return f"Error al verificar la agenda: {e}"

# Entrypoint estándar de Vercel Serverless
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        resultado = verificar_turnos()
        
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(resultado.encode('utf-8'))
        return