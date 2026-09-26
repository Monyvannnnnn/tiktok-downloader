import sqlalchemy
from config import DATABASE
from database.models import metadata
from services.logger import log_activity


def init_db():
    try:
        raw_db_url = DATABASE.replace("+aiomysql", "").replace("+aiosqlite", "")
        db_engine = sqlalchemy.create_engine(raw_db_url)
        metadata.create_all(db_engine)
        log_activity("Database tables initialized successfully.")
    except Exception as e:
        log_activity(f"Database table check/creation notice: {e}")
