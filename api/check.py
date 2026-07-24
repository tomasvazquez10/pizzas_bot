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
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Navegamos esperando a que la SPA cargue los datos
            page.goto(LINK_CALENDAR, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)
            
            # 1. Verificación global rápida en el cuerpo del texto
            body_text = page.inner_text("body").lower()
            if "no hay horarios disponibles" in body_text or "no available times" in body_text and not any(h in body_text for h in ["select a time", "selecciona un horario", "hs", "pm", "am"]):
                print("🔍 Chequeo realizado: Aún no hay turnos disponibles.")
                browser.close()
                return

            # 2. Capturamos todos los botones/elementos interactivos
            elementos = page.query_selector_all("button[aria-label], [role='button'][aria-label]")
            
            fechas_disponibles = []
            
            for elem in elementos:
                label = elem.get_attribute("aria-label") or ""
                label_lower = label.lower()
                
                # REGLA DE EXCLUSIÓN: Si dice "no available times" o "sin horarios", SE IGNORA
                if "no available times" in label_lower or "no hay horarios" in label_lower or "sin horarios" in label_lower:
                    continue

                # REGLA DE INCLUSIÓN: Debe indicar un turno o disponibilidad explícita
                # (Ejemplos: "available", o un horario concreto con "am"/"pm"/"hs")
                es_valido = (
                    ("available" in label_lower and "no available" not in label_lower) or
                    "disponible" in label_lower or
                    any(h in label_lower for h in [" am", " pm", " hs", ":00", ":30"])
                )

                if es_valido:
                    label_limpio = " ".join(label.split())
                    if label_limpio not in fechas_disponibles:
                        fechas_disponibles.append(label_limpio)

            browser.close()

            # Solo enviamos mensaje SI ENCONTRAMOS AL MENOS UN TURNO VÁLIDO
            if fechas_disponibles:
                lista_str = "\n".join([f"• 📅 <b>{f}</b>" for f in fechas_disponibles[:5]])
                msg = (
                    f"<b>¡TURNO DETECTADO EN GOOGLE CALENDAR!</b>\n\n"
                    f"<b>Fechas/Horarios disponibles encontrados:</b>\n{lista_str}\n\n"
                    f"🔗 <b>Reservá rápido acá:</b> {LINK_CALENDAR}"
                )
                print("🚀 ¡Turno REAL detectado! Enviando alerta a Telegram...")
                enviar_telegram(msg)
            else:
                print("🔍 Chequeo realizado: Se descartaron los botones 'no available times'. No hay turnos libres.")

    except Exception as e:
        print(f"❌ Error durante la verificación: {e}")

if __name__ == "__main__":
    verificar_turnos_playwright()
