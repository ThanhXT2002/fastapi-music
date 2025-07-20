from sqlalchemy import Column, String, Integer, DateTime, Text, Enum as SQLEnum, Index
from datetime import datetime
import enum
from app.config.database import Base

class ProcessingStatus(enum.Enum):
    PENDING = "pending"      # Đang chờ xử lý
    PROCESSING = "processing" # Đang tải
    COMPLETED = "completed"   # Hoàn thành
    FAILED = "failed"         # Thất bại

class Song(Base):
    __tablename__ = "songs"
    
    id = Column(String(50), primary_key=True)  # YouTube video ID
    title = Column(String(500), nullable=False)
    artist = Column(String(300), nullable=True)
    thumbnail_url = Column(Text, nullable=False)  # URL gốc từ YouTube
    duration = Column(Integer, nullable=False)    # Thời lượng (giây)
    duration_formatted = Column(String(20), nullable=False)  # Format MM:SS
    keywords = Column(Text, nullable=True)        # JSON string
    original_url = Column(Text, nullable=False)   # URL gốc
    
    # Processing status
    status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.PENDING, nullable=False)
    
    # File paths (null khi chưa tải xong)
    audio_filename = Column(String(300), nullable=True)
    thumbnail_filename = Column(String(300), nullable=True)
    
    # Error info
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Indexes for better performance
    __table_args__ = (
        Index('idx_songs_status', 'status'),
        Index('idx_songs_created_at', 'created_at'),
        Index('idx_songs_status_completed_at', 'status', 'completed_at'),
    )
