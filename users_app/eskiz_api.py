import requests
from django.conf import settings

import logging

class EskizAPI:
    def __init__(self):
        self.token = self.get_token()

    def get_token(self):
        response = requests.post(f"{settings.ESKIZ_BASE_URL}/api/auth/login", data={
            "email": settings.ESKIZ_EMAIL,
            "password": settings.ESKIZ_PASSWORD
        })
        if response.status_code == 200 and response.json().get("status") == "success":
            token = response.json().get("data", {}).get("token")
            logging.info("Authenticated with Eskiz API successfully.")
            return token
        else:
            logging.error(f"Failed to authenticate with Eskiz API: {response.json()}")
            return None  # Return None or handle this case as needed

    def send_sms(self, phone, message):
        if not self.token:
            logging.error("Eskiz API token is missing or invalid.")
            return {"error": "Authentication failed"}

        headers = {"Authorization": f"Bearer {self.token}"}
        data = {
            "mobile_phone": phone,
            "message": message,
            "from": "4546"  # Ensure this 'from' value is valid in Eskiz
        }
        response = requests.post(f"{settings.ESKIZ_BASE_URL}/api/message/sms/send", headers=headers, data=data)
        
        if response.status_code == 200:
            logging.info(f"SMS sent successfully to {phone}.")
        else:
            logging.error(f"Failed to send SMS: {response.json()}")

        return response.json()
