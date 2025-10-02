"""
Base model class with automatic ISO 8601 datetime serialization.
All models should extend this class to ensure consistent date formatting.
"""
from app.core.utils.json_encoder import serialize_model_dates


class BaseModel:
    """
    Base model class that provides automatic datetime serialization to ISO 8601 format.

    All model classes should extend this and implement to_dict() method.
    Call serialize_dates() at the end of to_dict() to ensure all datetime fields
    are properly formatted.

    Example:
        class User(BaseModel):
            def to_dict(self):
                data = {
                    'id': self.id,
                    'created_at': self.created_at,
                    'updated_at': self.updated_at
                }
                return self.serialize_dates(data)
    """

    @staticmethod
    def serialize_dates(data):
        """
        Serialize all datetime fields in the data to ISO 8601 format.

        This method should be called at the end of every to_dict() implementation
        to ensure consistent datetime formatting across all API responses.

        Args:
            data: Dictionary containing model data

        Returns:
            Dictionary with all datetime objects converted to ISO 8601 strings
        """
        return serialize_model_dates(data)
