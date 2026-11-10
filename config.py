import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
SUPPORT_URL = os.getenv("SUPPORT_URL", "https://t.me/")
PLAYEROK_URL = os.getenv("PLAYEROK_URL", "")
KWORK_URL = os.getenv("KWORK_URL", "")
DB_PATH = "shop.db"
