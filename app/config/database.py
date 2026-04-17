"""Cau hinh ket noi database va quan ly session.

Module nay chua:
- Khoi tao SQLAlchemy engine (ho tro SQLite va PostgreSQL).
- SessionLocal factory de tao database session.
- Dependency ``get_db`` dung trong FastAPI Depends.
- Ham tien ich: tao bang, kiem tra ket noi, lay thong tin DB.

Lien quan:
- Config: config.py (doc DATABASE_URL)
- Models: app/models/ (dang ky bang qua Base.metadata)
"""

# ── Standard library imports ──────────────────────────────
import re
import time

# ── Third-party imports ───────────────────────────────────
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ── Internal imports ──────────────────────────────────────
from app.config.config import settings


# ── Engine & Session ──────────────────────────────────────

if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        # SQLite khong ho tro multi-thread mac dinh
        connect_args={"check_same_thread": False},
        echo=False,
        pool_pre_ping=True,
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        # Recycle connection moi 1 gio de tranh stale connection
        pool_recycle=3600,
        pool_pre_ping=True,
        connect_args={"options": "-c timezone=utc"},
    )

SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)
Base = declarative_base()


# ── Connection utilities ──────────────────────────────────

def test_database_connection() -> bool:
    """Kiem tra ket noi database bang cach chay SELECT 1.

    Returns:
        True neu ket noi thanh cong, False neu that bai.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection test failed: {e}")
        return False


def get_db_with_retry(
    max_retries: int = 3, retry_delay: float = 1.0
):
    """Tao database session voi co che retry khi mat ket noi.

    Thu ket noi lai toi da ``max_retries`` lan, moi lan cach nhau
    ``retry_delay`` giay. Dung cho cac tinh huong database khoi
    dong cham hoac network khong on dinh.

    Args:
        max_retries: So lan thu lai toi da. Mac dinh 3.
        retry_delay: Thoi gian cho giua cac lan thu (giay).

    Yields:
        SQLAlchemy Session da kiem tra ket noi thanh cong.

    Raises:
        Exception: Khi vuot qua so lan retry cho phep.
    """
    for attempt in range(max_retries):
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            yield db
            break
        except Exception as e:
            print(
                f"Database connection attempt "
                f"{attempt + 1}/{max_retries} failed: {e}"
            )
            if hasattr('db', 'close'):
                db.close()
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                raise Exception(
                    f"Failed to connect to database "
                    f"after {max_retries} attempts"
                )
        finally:
            if 'db' in locals():
                db.close()


# ── Dependencies ──────────────────────────────────────────

def get_db():
    """Tao database session cho moi request (FastAPI Depends).

    Session duoc tu dong dong sau khi request ket thuc nho finally.
    Neu co loi ket noi, rollback truoc khi raise exception.

    Yields:
        SQLAlchemy Session.

    Raises:
        Exception: Khi khong the ket noi toi database.
    """
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


# ── Table management ──────────────────────────────────────

def create_tables():
    """Tao tat ca cac bang da dang ky trong Base.metadata."""
    Base.metadata.create_all(bind=engine)
    print(
        f"Database tables created successfully "
        f"using {get_database_type()}"
    )


def get_database_type() -> str:
    """Tra ve ten loai database dang su dung (VD: 'sqlite', 'postgresql')."""
    return engine.name


def get_database_info() -> dict:
    """Tra ve thong tin database de hien thi khi startup.

    Returns:
        Dict chua database_type, database_url, va database_file
        (chi co neu la SQLite).
    """
    info = {
        "database_type": get_database_type(),
        "database_url": settings.DATABASE_URL,
    }
    if settings.DATABASE_URL.startswith("sqlite"):
        match = re.search(r'sqlite:///([^"]+)', settings.DATABASE_URL)
        if match:
            info["database_file"] = match.group(1)
    return info
