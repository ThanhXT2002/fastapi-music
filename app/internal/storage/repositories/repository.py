from sqlalchemy.orm import Session
from typing import TypeVar, Generic, List, Optional, Any, Dict
from sqlalchemy.ext.declarative import DeclarativeMeta

T = TypeVar('T')

class BaseRepository(Generic[T]):
    def __init__(self, model: DeclarativeMeta, db: Session):
        self.model = model
        self.db = db
    
    def create(self, obj_data: Dict[str, Any]) -> T:
        """Create a new object"""
        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def find_by_id(self, obj_id: Any) -> Optional[T]:
        """Find object by ID"""
        return self.db.query(self.model).filter(self.model.id == obj_id).first()
    
    def find_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all objects with pagination"""
        return self.db.query(self.model).offset(skip).limit(limit).all()
    
    def update(self, obj_id: Any, obj_data: Dict[str, Any]) -> Optional[T]:
        """Update an object"""
        db_obj = self.find_by_id(obj_id)
        if db_obj:
            for key, value in obj_data.items():
                setattr(db_obj, key, value)
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj
    
    def delete(self, obj_id: Any) -> bool:
        """Delete an object"""
        db_obj = self.find_by_id(obj_id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
            return True
        return False
    
    def count(self) -> int:
        """Count total objects"""
        return self.db.query(self.model).count()
