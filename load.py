import os
import databases
from dotenv import load_dotenv

load_dotenv()

token_bot = os.environ.get("token_bot")
api_id_raw = os.environ.get("api_id")
api_id = int(api_id_raw) if api_id_raw and api_id_raw.strip().isdigit() else api_id_raw
api_hash = os.environ.get("api_hash")
database_type = os.getenv("database_type", "sqlite").lower()
database_url = os.getenv("database_url", "localhost")
database_port = os.getenv("database_port", "3306")
database_user = os.getenv("database_user", "")
database_pass = os.getenv("database_pass", "")
database_name = os.getenv("database_name", "tiktok-downloader")

if database_type == "sqlite" or not database_user:
    DATABASE = f"sqlite+aiosqlite:///{database_name}.db"
else:
    DATABASE = f"mysql+aiomysql://{database_user}:{database_pass}@{database_url}:{database_port}/{database_name}"
