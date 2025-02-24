import os
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")

def send_whatsapp_message(to, message):
    """ Enviar un mensaje de texto a WhatsApp usando la API de Meta """
    url = f"https://graph.facebook.com/v16.0/{WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": message}
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json()
