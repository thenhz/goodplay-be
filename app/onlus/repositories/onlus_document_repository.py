from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from app.core.repositories.base_repository import BaseRepository
from app.onlus.models.onlus_document import ONLUSDocument, DocumentStatus
import os


class ONLUSDocumentRepository(BaseRepository):
    """
    Repository for ONLUS document data access operations.
    Handles CRUD operations and document-specific queries.
    """

    def __init__(self):
        super().__init__('onlus_documents')

    def create_indexes(self):
        """Create database indexes for optimal query performance."""
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        # Create indexes for common queries
        self.collection.create_index("application_id")
        self.collection.create_index([("application_id", 1), ("document_type", 1)])
        self.collection.create_index("status")
        self.collection.create_index("upload_date")
        self.collection.create_index("expiration_date")
        self.collection.create_index([("status", 1), ("upload_date", -1)])
        self.collection.create_index("reviewed_by")
        self.collection.create_index("is_required")

    def find_by_application_id(self, application_id: str) -> List[ONLUSDocument]:
        """
        Find all documents for an application.

        Args:
            application_id: Application ID

        Returns:
            List[ONLUSDocument]: List of documents for the application
        """
        data_list = self.find_many(
            {"application_id": application_id},
            sort=[("upload_date", -1)]
        )
        return [ONLUSDocument.from_dict(data) for data in data_list]

    def find_by_application_and_type(self, application_id: str,
                                    document_type: str) -> List[ONLUSDocument]:
        """
        Find documents by application and type.

        Args:
            application_id: Application ID
            document_type: Document type

        Returns:
            List[ONLUSDocument]: Documents matching criteria
        """
        data_list = self.find_many(
            {
                "application_id": application_id,
                "document_type": document_type
            },
            sort=[("version", -1), ("upload_date", -1)]
        )
        return [ONLUSDocument.from_dict(data) for data in data_list]

    def create_document(self, document: ONLUSDocument) -> str:
        """
        Create a new document.

        Args:
            document: Document to create

        Returns:
            str: Created document ID
        """
        document_data = document.to_dict(include_sensitive=True)
        document_data.pop('_id', None)  # Remove _id to let MongoDB generate it
        return self.create(document_data)

    def update_document(self, document_id: str, document: ONLUSDocument) -> bool:
        """
        Update document.

        Args:
            document_id: Document ID to update
            document: Updated document

        Returns:
            bool: True if updated successfully, False otherwise
        """
        document_data = document.to_dict(include_sensitive=True)
        document_data.pop('_id', None)  # Remove _id from update data
        return self.update_by_id(document_id, document_data)

    def get_documents_by_status(self, status: str, limit: int = None) -> List[ONLUSDocument]:
        """
        Get documents by status.

        Args:
            status: Document status
            limit: Maximum number of documents to return

        Returns:
            List[ONLUSDocument]: Documents with specified status
        """
        data_list = self.find_many(
            {"status": status},
            sort=[("upload_date", -1)],
            limit=limit
        )
        return [ONLUSDocument.from_dict(data) for data in data_list]

    def get_pending_review_documents(self, reviewer_id: str = None) -> List[ONLUSDocument]:
        """
        Get documents pending review.

        Args:
            reviewer_id: Optional reviewer ID to filter by

        Returns:
            List[ONLUSDocument]: Documents pending review
        """
        filter_criteria = {"status": DocumentStatus.UNDER_REVIEW.value}
        if reviewer_id:
            filter_criteria["reviewed_by"] = reviewer_id

        data_list = self.find_many(
            filter_criteria,
            sort=[("upload_date", 1)]  # Oldest first
        )
        return [ONLUSDocument.from_dict(data) for data in data_list]

    def get_expired_documents(self) -> List[ONLUSDocument]:
        """
        Get documents that have expired.

        Returns:
            List[ONLUSDocument]: Expired documents
        """
        current_time = datetime.now(timezone.utc)
        data_list = self.find_many({
            "expiration_date": {"$lt": current_time},
            "status": {"$ne": DocumentStatus.EXPIRED.value}
        })
        return [ONLUSDocument.from_dict(data) for data in data_list]

    def get_expiring_documents(self, days: int = 30) -> List[ONLUSDocument]:
        """
        Get documents expiring within specified days.

        Args:
            days: Number of days to look ahead

        Returns:
            List[ONLUSDocument]: Documents expiring soon
        """
        current_time = datetime.now(timezone.utc)
        expiry_threshold = current_time + timedelta(days=days)

        data_list = self.find_many({
            "expiration_date": {
                "$gte": current_time,
                "$lte": expiry_threshold
            },
            "status": DocumentStatus.APPROVED.value
        })
        return [ONLUSDocument.from_dict(data) for data in data_list]

    def update_document_status(self, document_id: str, status: str,
                              reviewer_id: str = None, notes: str = None,
                              rejection_reason: str = None) -> bool:
        """
        Update document status.

        Args:
            document_id: Document ID
            status: New status
            reviewer_id: Reviewer ID
            notes: Reviewer notes
            rejection_reason: Rejection reason if applicable

        Returns:
            bool: True if updated successfully, False otherwise
        """
        update_data = {
            "status": status,
            "review_date": self._get_current_time(),
            "updated_at": self._get_current_time()
        }

        if reviewer_id:
            update_data["reviewed_by"] = reviewer_id
        if notes:
            update_data["reviewer_notes"] = notes
        if rejection_reason:
            update_data["rejection_reason"] = rejection_reason

        return self.update_by_id(document_id, update_data)

    def get_documents_by_reviewer(self, reviewer_id: str,
                                 limit: int = None) -> List[ONLUSDocument]:
        """
        Get documents reviewed by specific reviewer.

        Args:
            reviewer_id: Reviewer ID
            limit: Maximum number of documents to return

        Returns:
            List[ONLUSDocument]: Documents reviewed by reviewer
        """
        data_list = self.find_many(
            {"reviewed_by": reviewer_id},
            sort=[("review_date", -1)],
            limit=limit
        )
        return [ONLUSDocument.from_dict(data) for data in data_list]

    def get_application_document_stats(self, application_id: str) -> Dict[str, Any]:
        """
        Get document statistics for an application.

        Args:
            application_id: Application ID

        Returns:
            Dict[str, Any]: Document statistics
        """
        if not self.collection:
            return {}

        try:
            pipeline = [
                {"$match": {"application_id": application_id}},
                {
                    "$group": {
                        "_id": "$status",
                        "count": {"$sum": 1},
                        "total_size": {"$sum": "$file_size"}
                    }
                }
            ]

            results = list(self.collection.aggregate(pipeline))
            stats = {
                "total_documents": 0,
                "total_size": 0,
                "by_status": {}
            }

            for result in results:
                status = result["_id"]
                count = result["count"]
                size = result["total_size"]

                stats["total_documents"] += count
                stats["total_size"] += size
                stats["by_status"][status] = {
                    "count": count,
                    "size": size
                }

            return stats

        except Exception:
            return {
                "total_documents": 0,
                "total_size": 0,
                "by_status": {}
            }

    def get_document_types_for_application(self, application_id: str) -> List[str]:
        """
        Get list of document types for an application.

        Args:
            application_id: Application ID

        Returns:
            List[str]: List of document types
        """
        if not self.collection:
            return []

        try:
            pipeline = [
                {"$match": {"application_id": application_id}},
                {"$group": {"_id": "$document_type"}},
                {"$sort": {"_id": 1}}
            ]

            results = list(self.collection.aggregate(pipeline))
            return [result["_id"] for result in results]

        except Exception:
            return []

    def mark_documents_as_expired(self) -> int:
        """
        Mark expired documents as expired.

        Returns:
            int: Number of documents marked as expired
        """
        current_time = datetime.now(timezone.utc)

        try:
            result = self.collection.update_many(
                {
                    "expiration_date": {"$lt": current_time},
                    "status": {"$ne": DocumentStatus.EXPIRED.value}
                },
                {
                    "$set": {
                        "status": DocumentStatus.EXPIRED.value,
                        "updated_at": current_time
                    }
                }
            )
            return result.modified_count
        except Exception:
            return 0

    def get_latest_document_version(self, application_id: str,
                                   document_type: str) -> Optional[ONLUSDocument]:
        """
        Get the latest version of a document type for an application.

        Args:
            application_id: Application ID
            document_type: Document type

        Returns:
            Optional[ONLUSDocument]: Latest document version if found
        """
        data = self.find_one(
            {
                "application_id": application_id,
                "document_type": document_type
            },
            sort=[("version", -1), ("upload_date", -1)]
        )
        return ONLUSDocument.from_dict(data) if data else None

    def get_required_documents_status(self, application_id: str,
                                     required_types: List[str]) -> Dict[str, str]:
        """
        Get status of required documents for an application.

        Args:
            application_id: Application ID
            required_types: List of required document types

        Returns:
            Dict[str, str]: Document type to status mapping
        """
        status_map = {}

        for doc_type in required_types:
            latest_doc = self.get_latest_document_version(application_id, doc_type)
            status_map[doc_type] = latest_doc.status if latest_doc else "missing"

        return status_map