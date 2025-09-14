from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from bson import ObjectId
from app import get_db

class BaseRepository(ABC):
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self.db = get_db()
        self.collection = self.db[collection_name] if self.db is not None else None
    
    def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        if not ObjectId.is_valid(id):
            return None
        return self.collection.find_one({"_id": ObjectId(id)})
    
    def find_one(self, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self.collection.find_one(filter_dict)
    
    def find_many(self, filter_dict: Dict[str, Any] = None, 
                  limit: int = None, skip: int = None, 
                  sort: List[tuple] = None) -> List[Dict[str, Any]]:
        filter_dict = filter_dict or {}
        cursor = self.collection.find(filter_dict)
        
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
            
        return list(cursor)
    
    def create(self, data: Dict[str, Any]) -> str:
        result = self.collection.insert_one(data)
        return str(result.inserted_id)
    
    def update_by_id(self, id: str, data: Dict[str, Any]) -> bool:
        if not ObjectId.is_valid(id):
            return False
        result = self.collection.update_one(
            {"_id": ObjectId(id)}, 
            {"$set": data}
        )
        return result.modified_count > 0
    
    def update_one(self, filter_dict: Dict[str, Any], 
                   data: Dict[str, Any]) -> bool:
        result = self.collection.update_one(filter_dict, {"$set": data})
        return result.modified_count > 0
    
    def delete_by_id(self, id: str) -> bool:
        if not ObjectId.is_valid(id):
            return False
        result = self.collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0
    
    def delete_one(self, filter_dict: Dict[str, Any]) -> bool:
        result = self.collection.delete_one(filter_dict)
        return result.deleted_count > 0
    
    def count(self, filter_dict: Dict[str, Any] = None) -> int:
        filter_dict = filter_dict or {}
        return self.collection.count_documents(filter_dict)
    
    @abstractmethod
    def create_indexes(self):
        pass