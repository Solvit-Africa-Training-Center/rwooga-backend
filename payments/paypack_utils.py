import requests
import json
from django.conf import settings
from decouple import config
import time


class PaypackService:
    BASE_URL = "https://payments.paypack.rw/api"

    def __init__(self):
        # Check if we're in sandbox/test mode
        self.mode = config('PAYPACK_MODE', default='production')

        if self.mode == 'sandbox':
            self.client_id = config('PAYPACK_SANDBOX_CLIENT_ID', default=config('PAYPACK_CLIENT_ID'))
            self.client_secret = config('PAYPACK_SANDBOX_CLIENT_SECRET', default=config('PAYPACK_CLIENT_SECRET'))
            print("PAYPACK SANDBOX MODE - Using test credentials")
        else:
            self.client_id = config('PAYPACK_CLIENT_ID')
            self.client_secret = config('PAYPACK_CLIENT_SECRET')
            print("PAYPACK PRODUCTION MODE - Using live credentials")

        self.token = None
        self.token_expiry = 0

    def _normalize_phone(self, phone_number):
        
        phone = phone_number.strip().replace(' ', '').replace('-', '')

        if phone.startswith('+250'):
            phone = '0' + phone[4:]
        elif phone.startswith('250'):
            phone = '0' + phone[3:]

        return phone

    def authenticate(self):
        
        if self.token and time.time() < self.token_expiry:
            return self.token

        url = f"{self.BASE_URL}/auth/agents/authorize"

        try:
            response = requests.post(url, json={
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }, timeout=30)

            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access')             
                expires_in = data.get('expires_in', 2100)
                self.token_expiry = time.time() + min(expires_in, 2100) - 60
                print("Paypack authentication successful")
                return self.token
            else:
                print(f"Paypack Authentication Failed [{response.status_code}]: {response.text}")
                return None

        except requests.exceptions.Timeout:
            print("Paypack Auth Error: Request timed out")
            return None
        except Exception as e:
            print(f"Paypack Auth Error: {str(e)}")
            return None

    def _force_refresh(self):
        """Clear cached token and force a fresh authentication."""
        self.token = None
        self.token_expiry = 0
        return self.authenticate()

    def cashin(self, amount, phone_number, attempt_reference=None):
        
        token = self.authenticate()
        if not token:
            return {"ok": False, "error": "Authentication failed"}

        url = f"{self.BASE_URL}/transactions/cashin"

        # Normalize phone number to format Paypack expects: 07XXXXXXXX
        normalized_phone = self._normalize_phone(phone_number)

        payload = {
            "amount": float(amount),
            "number": normalized_phone,
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            print(f"DEBUG: Initiating Cashin | number={normalized_phone} | amount={amount}")
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            print(f"DEBUG: Paypack Response Status: {response.status_code}")
            print(f"DEBUG: Paypack Response Body: {response.text}")

            # If token expired mid-session, force refresh and retry once
            if response.status_code == 401:
                print("Paypack Cashin: Token expired, refreshing and retrying...")
                token = self._force_refresh()
                if not token:
                    return {"ok": False, "error": "Re-authentication failed"}
                headers["Authorization"] = f"Bearer {token}"
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                print(f"DEBUG: Paypack Retry Response Status: {response.status_code}")
                print(f"DEBUG: Paypack Retry Response Body: {response.text}")

            data = response.json()

            if response.status_code == 200:
                return {
                    "ok": True,
                    "ref": data.get('ref'),
                    "status": data.get('status'),
                    "amount": data.get('amount'),
                }
            else:
                print(f"Paypack Cashin Failed [{response.status_code}]: {response.text}")
                return {
                    "ok": False,
                    "error": "Payment request failed",
                    "details": data,
                }

        except requests.exceptions.Timeout:
            print("Paypack Cashin Error: Request timed out")
            return {"ok": False, "error": "Payment provider timed out. Please try again."}
        except Exception as e:
            print(f"Paypack Cashin Error: {str(e)}")
            return {"ok": False, "error": str(e)}

    def cashout(self, amount, phone_number):
     
        token = self.authenticate()
        if not token:
            return {"ok": False, "error": "Authentication failed"}

        url = f"{self.BASE_URL}/transactions/cashout"

        normalized_phone = self._normalize_phone(phone_number)

        payload = {
            "amount": float(amount),
            "number": normalized_phone,
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            print(f"DEBUG: Initiating Cashout | number={normalized_phone} | amount={amount}")
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            print(f"DEBUG: Paypack Cashout Response Status: {response.status_code}")
            print(f"DEBUG: Paypack Cashout Response Body: {response.text}")

            # If token expired mid-session, force refresh and retry once
            if response.status_code == 401:
                print("Paypack Cashout: Token expired, refreshing and retrying...")
                token = self._force_refresh()
                if not token:
                    return {"ok": False, "error": "Re-authentication failed"}
                headers["Authorization"] = f"Bearer {token}"
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                print(f"DEBUG: Paypack Cashout Retry Response Status: {response.status_code}")
                print(f"DEBUG: Paypack Cashout Retry Response Body: {response.text}")

            data = response.json()

            if response.status_code == 200:
                return {
                    "ok": True,
                    "ref": data.get('ref'),
                    "status": data.get('status'),
                    "amount": data.get('amount'),
                }
            else:
                print(f"Paypack Cashout Failed [{response.status_code}]: {response.text}")
                return {
                    "ok": False,
                    "error": "Cashout request failed",
                    "details": data,
                }

        except requests.exceptions.Timeout:
            print("Paypack Cashout Error: Request timed out")
            return {"ok": False, "error": "Payment provider timed out. Please try again."}
        except Exception as e:
            print(f"Paypack Cashout Error: {str(e)}")
            return {"ok": False, "error": str(e)}

    def check_status(self, ref):
        
        token = self.authenticate()
        if not token:
            return None

        url = f"{self.BASE_URL}/events/transactions?ref={ref}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(url, headers=headers, timeout=30)

            # If token expired mid-session, force refresh and retry once
            if response.status_code == 401:
                print("Paypack Status Check: Token expired, refreshing and retrying...")
                token = self._force_refresh()
                if not token:
                    return None
                headers["Authorization"] = f"Bearer {token}"
                response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                # Return the most recent transaction if multiple exist
                transactions = data.get('transactions')
                if transactions and len(transactions) > 0:
                    return transactions[0]
                return data
            else:
                print(f"Paypack Status Check Failed [{response.status_code}]: {response.text}")
                return None

        except requests.exceptions.Timeout:
            print("Paypack Status Check Error: Request timed out")
            return None
        except Exception as e:
            print(f"Paypack Status Check Error: {str(e)}")
            return None



paypack_service = PaypackService()