from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config.config import settings
import time
from typing import Optional

# Import V2 models to ensure they are registered
try:
    from app.api.v2.models.song import SongV2, DownloadLogV2
except ImportError:
    # V2 models not available yet
    pass

# Import V3 models to ensure they are registered
try:
    from app.api.v3.models.song import SongV3
except ImportError:
    # V3 models not available yet
    pass

# Enhanced engine configuration for both SQLite and PostgreSQL
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite specific configuration
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},  # SQLite specific
        echo=False,  # Set to True for debugging
        pool_pre_ping=True
    )
else:
    # PostgreSQL configuration
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=10,                    # Number of connections to maintain
        max_overflow=20,                 # Additional connections beyond pool_size
        pool_timeout=30,                 # Seconds to wait for connection
        pool_recycle=3600,              # Recycle connections every hour
        pool_pre_ping=True,             # Test connections before use
        connect_args={
            "options": "-c timezone=utc"  # Set timezone for PostgreSQL
        }
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def test_database_connection() -> bool:
    """
    Test if database connection is working
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection test failed: {e}")
        return False

def get_db_with_retry(max_retries: int = 3, retry_delay: float = 1.0):
    """
    Database session dependency with retry logic
    """
    for attempt in range(max_retries):
        try:
            db = SessionLocal()
            # Test the connection
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
    """
    Database session dependency with enhanced error handling
    """
    db = SessionLocal()
    try:
        # Test the connection
        db.execute(text("SELECT 1"))
        yield db
    except Exception as e:
        print(f"Database connection error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    print(f"Database tables created successfully using {get_database_type()}")

def get_database_type():
    """Get database type"""
    if settings.DATABASE_URL.startswith("sqlite"):
        return "SQLite"
    elif settings.DATABASE_URL.startswith("postgresql"):
        return "PostgreSQL"
    else:
        return "Unknown"

def get_database_info():
    """Get database connection info"""
    db_type = get_database_type()
    info = {
        "database_url": settings.DATABASE_URL,
        "database_type": db_type,
    }
    
    if db_type == "SQLite":
        info["database_file"] = settings.DATABASE_URL.split("///")[-1]
    
    return info
