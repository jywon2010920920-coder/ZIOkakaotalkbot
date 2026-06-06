import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PORT: int          = int(os.getenv("PORT", "8000"))
    BRAWL_API_KEY: str = os.getenv("BRAWL_API_KEY", "")
    KAKAO_EMAIL: str   = os.getenv("KAKAO_EMAIL", "")
    KAKAO_PASSWORD: str = os.getenv("KAKAO_PASSWORD", "")
    KAKAO_ROOM_ID: str = os.getenv("KAKAO_ROOM_ID", "")

settings = Settings()
