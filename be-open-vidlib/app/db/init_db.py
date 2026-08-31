import logging
from sqlalchemy import text
from app.core.database import Base, engine, SessionLocal
from app.db.seed import seed_database

logger = logging.getLogger(__name__)

def init_db():
    """Create all database tables and seed initial data if empty."""
    try:
        if engine.dialect.name == "postgresql":
            with engine.begin() as connection:
                connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            seed_database(db)
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
