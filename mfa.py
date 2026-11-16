import json
import time
import httpx

# ---------------------- AYARLAR ----------------------
CONFIG = {
    "token": "BURAYA_TOKEN_GIRIN",
    "server_id": "BURAYA_SERVER_ID_GIRIN",
    "password": "BURAYA_SIFRE_GIRIN",
    "refresh_interval_minutes": 2
}

SUPER_PROPERTIES = "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiRmlyZWZveCIsImRldmljZSI6IiIsInN5c3RlbV9sb2NhbGUiOiJ0ci1UUiIsImJyb3dzZXJfdXNlcl9hZ2VudCI6Ik1vemlsbGEvNS4wIChXaW5kb3dzIE5UIDEwLjA7IFdpbjY0OyB4NjQ7IHJ2OjEzMy4wKSBHZWNrby8yMDEwMDEwMSBGaXJlZm94LzEzMy4wIiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTMzLjAiLCJvc192ZXJzaW9uIjoiMTAiLCJyZWZlcnJlciI6Imh0dHBzOi8vd3d3Lmdvb2dsZS5jb20vIiwicmVmZXJyaW5nX2RvbWFpbiI6Ind3dy5nb29nbGUuY29tIiwic2VhcmNoX2VuZ2luZSI6Imdvb2dsZSIsInJlZmVycmVyX2N1cnJlbnQiOiIiLCJyZWxlYXNlX2NoYW5uZWwiOiJjYW5hcnkiLCJjbGllbnRfYnVpbGRfbnVtYmVyIjozNTYxNDAsImNsaWVudF9ldmVudF9zb3VyY2UiOm51bGwsImhhc19jbGllbnRfbW9kcyI6ZmFsc2V9"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0"

class MfaManager:
    def __init__(self, token: str, server_id: str, password: str):
        self.token = token
        self.server_id = server_id
        self.password = password
        self.mfa_token = None
        
        # HTTP/2 oturumu
        self.client = httpx.Client(
            http2=True,
            verify=False,
            headers={
                "User-Agent": USER_AGENT,
                "Authorization": self.token,
                "Content-Type": "application/json",
                "X-Super-Properties": SUPER_PROPERTIES
            },
            timeout=10.0
        )

    def refresh(self) -> str:
        if not self.password or not self.server_id or not self.token:
            print("[!] Bilgiler eksik.")
            return None

        try:
            # 1. Asama: /api/v7 uzerinden ticket tetikle
            url_ticket = f"https://canary.discord.com/api/v7/guilds/{self.server_id}/vanity-url"
            res_ticket = self.client.patch(url_ticket)
            data_ticket = res_ticket.json()

            if data_ticket.get("code") == 60003 and "mfa" in data_ticket:
                ticket = data_ticket["mfa"].get("ticket")

                # 2. Asama: /api/v9/mfa/finish ile ticket'i sifreyle onayla
                url_finish = "https://canary.discord.com/api/v9/mfa/finish"
                payload = {
                    "ticket": ticket,
                    "mfa_type": "password",
                    "data": self.password
                }
                res_finish = self.client.post(url_finish, json=payload)
                data_finish = res_finish.json()

                if "token" in data_finish:
                    self.mfa_token = data_finish["token"]
                    print(f"\033[32m[+] MFA Token Basariyla Alindi:\033[0m {self.mfa_token}")
                    return self.mfa_token
                else:
                    print("\033[31m[-] Onaylama Hatasi:\033[0m", res_finish.text)
            elif "token" in data_ticket:
                self.mfa_token = data_ticket["token"]
                print(f"\033[32m[+] Dogrudan Token Alindi:\033[0m {self.mfa_token}")
                return self.mfa_token
            else:
                print("\033[33m[!] Beklenmeyen Yanit:\033[0m", res_ticket.text)

        except Exception as e:
            print("\033[31m[-] Hata:\033[0m", str(e))

        return None

    def get_token(self) -> str:
        return self.mfa_token


if __name__ == "__main__":
    mfa = MfaManager(
        token=CONFIG["token"],
        server_id=CONFIG["server_id"],
        password=CONFIG["password"]
    )

    while True:
        mfa.refresh()
        time.sleep(CONFIG["refresh_interval_minutes"] * 60)
