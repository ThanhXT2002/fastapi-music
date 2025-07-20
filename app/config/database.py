from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config.config import settings
import time
from typing import Optional

# Enhanced engine configuration for both SQLite and PostgreSQL
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
        pool_pre_ping=True
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=3600,
        pool_pre_ping=True,
        connect_args={
            "options": "-c timezone=utc"
        }
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def test_database_connection() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection test failed: {e}")
        return False

def get_db_with_retry(max_retries: int = 3, retry_delay: float = 1.0):
    for attempt in range(max_retries):
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            yield db
            break
        except Exception as e:
            print(f"Database connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if hasattr('db', 'close'):
                db.close()
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                raise Exception(f"Failed to connect to database after {max_retries} attempts")
        finally:
            if 'db' in locals():
                db.close()

def get_db():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        yield db
    except Exception as e:
        print(f"Database connection error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)
    print(f"Database tables created successfully using {get_database_type()}")

def get_database_type():
    return engine.name

def get_database_info():
    """Trả về thông tin database cho main.py"""
    info = {
        "database_type": get_database_type(),
        "database_url": settings.DATABASE_URL
    }
    # Nếu là SQLite, trả về file path
    if settings.DATABASE_URL.startswith("sqlite"):
        import re
        match = re.search(r'sqlite:///([^"]+)', settings.DATABASE_URL)
        if match:
            info["database_file"] = match.group(1)
    return info
