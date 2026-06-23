"""
Helper de configuración del bot de Telegram.
Ejecutar una sola vez para obtener tu chat_id y verificar que el bot funciona.

Pasos:
  1. Abre Telegram → busca @BotFather → escribe /newbot → sigue instrucciones
  2. Copia el token que te da BotFather
  3. Añade al .env (raíz del proyecto): TELEGRAM_BOT_TOKEN=<tu_token>
  4. Envía cualquier mensaje a tu nuevo bot en Telegram
  5. Ejecuta: venv\\Scripts\\python.exe financial_analyzer/alerts_engine/setup_telegram.py
  6. Copia el TELEGRAM_CHAT_ID que aparece y añádelo al .env
"""
import os
import sys
import requests
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

    if not token:
        print("\nERROR TELEGRAM_BOT_TOKEN no encontrado en el .env")
        print("\nPasos para crear el bot:")
        print("  1. Abre Telegram y busca @BotFather")
        print("  2. Escribe /newbot y sigue las instrucciones")
        print("  3. Copia el token que te da (parece: 123456789:ABCdef...)")
        print("  4. Añade al .env: TELEGRAM_BOT_TOKEN=<token>")
        print("  5. Vuelve a ejecutar este script")
        return

    print(f"\nOK Token encontrado: {token[:20]}...")

    url = f"https://api.telegram.org/bot{token}/getUpdates"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
    except Exception as e:
        print(f"\nERROR Error de conexión: {e}")
        return

    if not data.get("ok"):
        print(f"\nERROR Token inválido: {data.get('description')}")
        print("   Revisa que copiaste el token correctamente.")
        return

    updates = data.get("result", [])
    if not updates:
        print("\nAVISO  No hay mensajes en el bot.")
        print("   Envía cualquier mensaje a tu bot en Telegram y luego vuelve a ejecutar.")
        return

    # Obtener el chat_id del último mensaje
    chat = updates[-1]["message"]["chat"]
    chat_id = chat["id"]
    chat_name = chat.get("first_name") or chat.get("title") or "?"

    print(f"\nOK Chat ID: {chat_id}  (usuario: {chat_name})")
    print(f"\nAñade esto al .env (raíz del proyecto):")
    print(f"  TELEGRAM_CHAT_ID={chat_id}")

    # Enviar mensaje de prueba
    test_url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r2 = requests.post(test_url, json={
            "chat_id": chat_id,
            "text": (
                "OK <b>Bot de Alertas IA configurado correctamente</b>\n\n"
                "Recibirás aquí las alertas del sistema Financial Analyzer.\n"
                "<i>AVISO Solo informativo. No es asesoramiento financiero.</i>"
            ),
            "parse_mode": "HTML",
        }, timeout=10)

        if r2.status_code == 200:
            print("\nOK Mensaje de prueba enviado. ¡Comprueba Telegram!")
        else:
            print(f"\nAVISO  No se pudo enviar el mensaje de prueba: {r2.text}")
    except Exception as e:
        print(f"\nAVISO  Error enviando prueba: {e}")

    print("\n─── Configuración completa ───")
    print("Ahora puedes ejecutar:")
    print("  venv\\Scripts\\python.exe financial_analyzer/alerts_engine/runner.py --dry-run")


if __name__ == "__main__":
    main()
