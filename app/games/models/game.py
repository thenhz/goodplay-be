from datetime import datetime
from typing import Dict, Any, Optional
from bson import ObjectId
from dataclasses import dataclass, field

@dataclass
class Game:
    """Game model representing a game in the database"""
    name: str
    description: str
    category: str
    version: str
    is_active: bool = True
    credit_rate: float = 1.0  # Credits per minute
    author: str = ""
    plugin_id: str = ""
    min_players: int = 1
    max_players: int = 1
    estimated_duration_minutes: int = 10
    difficulty_level: str = "medium"  # easy, medium, hard
    requires_internet: bool = False
    instructions: str = ""
    install_count: int = 0
    rating: float = 0.0
    total_ratings: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    _id: Optional[ObjectId] = field(default=None)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the game to a dictionary for MongoDB storage"""
        data = {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "version": self.version,
            "is_active": self.is_active,
            "credit_rate": self.credit_rate,
            "author": self.author,
            "plugin_id": self.plugin_id,
            "min_players": self.min_players,
            "max_players": self.max_players,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "difficulty_level": self.difficulty_level,
            "requires_internet": self.requires_internet,
            "instructions": self.instructions,
            "install_count": self.install_count,
            "rating": self.rating,
            "total_ratings": self.total_ratings,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

        if self._id:
            data["_id"] = self._id

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Game':
        """Create a Game instance from a dictionary"""
        game = cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            category=data.get("category", ""),
            version=data.get("version", ""),
            is_active=data.get("is_active", True),
            credit_rate=data.get("credit_rate", 1.0),
            author=data.get("author", ""),
            plugin_id=data.get("plugin_id", ""),
            min_players=data.get("min_players", 1),
            max_players=data.get("max_players", 1),
            estimated_duration_minutes=data.get("estimated_duration_minutes", 10),
            difficulty_level=data.get("difficulty_level", "medium"),
            requires_internet=data.get("requires_internet", False),
            instructions=data.get("instructions", ""),
            install_count=data.get("install_count", 0),
            rating=data.get("rating", 0.0),
            total_ratings=data.get("total_ratings", 0),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow())
        )

        if "_id" in data:
            game._id = data["_id"]

        return game

    def to_api_dict(self) -> Dict[str, Any]:
        """Convert the game to a dictionary for API responses"""
        return {
            "id": str(self._id) if self._id else None,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "version": self.version,
            "is_active": self.is_active,
            "credit_rate": self.credit_rate,
            "author": self.author,
            "plugin_id": self.plugin_id,
            "min_players": self.min_players,
            "max_players": self.max_players,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "difficulty_level": self.difficulty_level,
            "requires_internet": self.requires_internet,
            "instructions": self.instructions,
            "install_count": self.install_count,
            "rating": self.rating,
            "total_ratings": self.total_ratings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    def update_rating(self, new_rating: float) -> None:
        """Update the game's average rating with a new rating"""
        total_score = self.rating * self.total_ratings
        self.total_ratings += 1
        self.rating = (total_score + new_rating) / self.total_ratings
        self.updated_at = datetime.utcnow()

    def increment_install_count(self) -> None:
        """Increment the install count for this game"""
        self.install_count += 1
        self.updated_at = datetime.utcnow()

    def update_version(self, new_version: str) -> None:
        """Update the game version"""
        self.version = new_version
        self.updated_at = datetime.utcnow()

    def set_active_status(self, is_active: bool) -> None:
        """Set the active status of the game"""
        self.is_active = is_active
        self.updated_at = datetime.utcnow()

    def __str__(self) -> str:
        return f"Game(id={self._id}, name={self.name}, version={self.version})"

    def __repr__(self) -> str:
        return self.__str__()