import os
import json
import re
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

def buscar_fechas_en_html(html_text):
    """
    Busca patrones de fechas / horarios en el JSON o texto embebido de Google Calendar.
    Ejemplos de patrones habituales: YYYY-MM-DD, fechas en formato ISO o timestamps.
    """
    fechas_encontradas = []
    
    # Busca patrones ISO tipo 2026-08-10T14:00:00
    patron_iso = r'\b202[6-9]-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])T(?:[01]\d|2[0-3]):[05]\d\b'
    coincidencias = re.findall(patron_iso, html_text)
    
    if coincidencias:
        # Eliminamos duplicados manteniendo el orden
        for f in coincidencias:
            if f not in fechas_encontradas:
                fechas_encontradas.append(f)
                
    return fechas_encontradas

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
            # Intentamos extraer fechas exactas del contenido
            fechas = buscar_fechas_en_html(html)
            
            if fechas:
                # Formateamos las fechas encontradas
                lista_fechas = "\n".join([f"• 📅 <b>{f}</b>" for f in fechas[:5]])
                texto_fechas = f"Fechas/Horarios detectados:\n{lista_fechas}"
            else:
                texto_fechas = "Se detectaron espacios habilitados en la agenda."

            msg = (
                f"<b>¡TURNO DETECTADO EN GOOGLE CALENDAR!</b>\n\n"
                f"{texto_fechas}\n\n"
                f"🔗 <b>Reservá rápido acá:</b> {LINK_CALENDAR}"
            )
            print("🚀 ¡Turno detectado! Enviando alerta con fechas...")
            enviar_telegram(msg)
        else:
            print("🔍 Chequeo realizado: Aún no hay turnos disponibles.")

    except Exception as e:
        print(f"❌ Error al verificar la agenda: {e}")

if __name__ == "__main__":
    verificar_turnos()
