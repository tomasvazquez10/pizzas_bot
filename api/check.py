import os
import requests
from playwright.sync_api import sync_playwright

LINK_CALENDAR = "https://calendar.app.google/URnpmiyiKZtAurqP8"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

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

def verificar_turnos_playwright():
    try:
        with sync_playwright() as p:
            # Lanzamos navegador Chromium en modo Headless
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Navegamos al link esperando a que la red esté inactiva (cargue completa de JS)
            page.goto(LINK_CALENDAR, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000) # Espera de cortesía de 3 segundos
            
            # 1. Chequeo de texto general si no hay disponibilidad
            body_text = page.inner_text("body")
            if "No hay horarios disponibles" in body_text or "No available times" in body_text:
                print("🔍 Chequeo realizado: Aún no hay turnos disponibles.")
                browser.close()
                return

            # 2. Buscar elementos interactivos de días/turnos con aria-label o botones activos
            elementos = page.query_selector_all("button[aria-label], [role='button'][aria-label], button[data-timestamp]")
            
            fechas_detectadas = []
            for elem in elementos:
                label = elem.get_attribute("aria-label") or elem.inner_text()
                if label and any(palabra in label.lower() for palabra in ["disponible", "available", "hs", "pm", "am", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]):
                    # Limpiamos saltos de línea extra
                    label_limpio = " ".join(label.split())
                    if label_limpio not in fechas_detectadas:
                        fechas_detectadas.append(label_limpio)

            browser.close()

            if fechas_detectadas:
                lista_str = "\n".join([f"• 📅 <b>{f}</b>" for f in fechas_detectadas[:5]])
                msg = (
                    f"<b>¡TURNO DETECTADO EN GOOGLE CALENDAR!</b>\n\n"
                    f"<b>Fechas/Horarios disponibles encontrados:</b>\n{lista_str}\n\n"
                    f"🔗 <b>Reservá rápido acá:</b> {LINK_CALENDAR}"
                )
            else:
                msg = (
                    f"<b>¡TURNO DETECTADO EN GOOGLE CALENDAR!</b>\n\n"
                    f"Se detectó un espacio libre en la agenda, pero no se pudo formatear el texto de la fecha.\n\n"
                    f"🔗 <b>Entrá directo a revisar:</b> {LINK_CALENDAR}"
                )

            print("🚀 Turno detectado. Enviando alerta a Telegram...")
            enviar_telegram(msg)

    except Exception as e:
        print(f"❌ Error durante el scraping con Playwright: {e}")

if __name__ == "__main__":
    verificar_turnos_playwright()
