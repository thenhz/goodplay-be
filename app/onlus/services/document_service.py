from typing import Tuple, Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from flask import current_app
from app.onlus.repositories.onlus_document_repository import ONLUSDocumentRepository
from app.onlus.repositories.onlus_application_repository import ONLUSApplicationRepository
from app.onlus.models.onlus_document import ONLUSDocument, DocumentStatus, DocumentType, DocumentFormat
from app.onlus.models.onlus_application import ApplicationStatus


class DocumentService:
    """
    Service for ONLUS document management.
    Handles document upload, validation, review, and lifecycle management.
    """

    def __init__(self):
        self.document_repo = ONLUSDocumentRepository()
        self.application_repo = ONLUSApplicationRepository()

    def upload_document(self, application_id: str, document_data: Dict[str, Any],
                       user_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Upload a document for an application.

        Args:
            application_id: Application ID
            document_data: Document upload data
            user_id: User uploading the document

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, document data
        """
        try:
            # Get application to verify ownership
            application = self.application_repo.find_by_id(application_id)
            if not application:
                return False, "APPLICATION_NOT_FOUND", None

            application_obj = application
            if isinstance(application, dict):
                from app.onlus.models.onlus_application import ONLUSApplication
                application_obj = ONLUSApplication.from_dict(application)

            # Check authorization
            if user_id != application_obj.applicant_id:
                return False, "DOCUMENT_UPLOAD_ACCESS_DENIED", None

            # Check if application allows document uploads
            if application_obj.status not in [
                ApplicationStatus.DRAFT.value,
                ApplicationStatus.DOCUMENTATION_PENDING.value
            ]:
                return False, "DOCUMENT_UPLOAD_NOT_ALLOWED", None

            # Add application ID to document data
            document_data['application_id'] = application_id

            # Validate document data
            validation_error = ONLUSDocument.validate_document_data(document_data)
            if validation_error:
                current_app.logger.warning(f"Document validation failed: {validation_error}")
                return False, validation_error, None

            # Check if document type is required for this application
            document_type = document_data['document_type']
            if document_type not in application_obj.required_documents:
                current_app.logger.warning(f"Document type not required: {document_type}")
                return False, "DOCUMENT_TYPE_NOT_REQUIRED", None

            # Check for existing document of same type
            existing_docs = self.document_repo.find_by_application_and_type(
                application_id, document_type
            )

            # Determine version number
            version = 1
            if existing_docs:
                latest_version = max(doc.version for doc in existing_docs)
                version = latest_version + 1

                # Mark previous version as superseded
                for doc in existing_docs:
                    if doc.version == latest_version:
                        doc.status = "superseded"
                        self.document_repo.update_document(str(doc._id), doc)

            # Set document metadata
            document_data['version'] = version
            document_data['upload_date'] = datetime.now(timezone.utc)

            # Set expiration date for documents that expire
            if self._document_expires(document_type):
                document_data['expiration_date'] = datetime.now(timezone.utc) + timedelta(days=365)

            # Create document instance
            document = ONLUSDocument(**document_data)

            # Save document
            document_id = self.document_repo.create_document(document)

            # Update application with document reference
            if document_id not in application_obj.submitted_documents:
                application_obj.add_document(document_id)
                application_obj.calculate_completion_percentage()
                self.application_repo.update_application(application_id, application_obj)

            current_app.logger.info(f"Document uploaded: {document_id} for application {application_id}")

            return True, "DOCUMENT_UPLOADED_SUCCESS", {
                "document_id": document_id,
                "document_type": document.document_type,
                "filename": document.filename,
                "version": document.version,
                "status": document.status,
                "upload_date": document.upload_date
            }

        except Exception as e:
            current_app.logger.error(f"Failed to upload document: {str(e)}")
            return False, "DOCUMENT_UPLOAD_FAILED", None

    def get_application_documents(self, application_id: str, user_id: str = None,
                                is_admin: bool = False) -> Tuple[bool, str, Optional[List[Dict]]]:
        """
        Get all documents for an application.

        Args:
            application_id: Application ID
            user_id: User ID (for authorization)
            is_admin: Whether user is admin

        Returns:
            Tuple[bool, str, Optional[List[Dict]]]: Success, message, documents list
        """
        try:
            # Check authorization if not admin
            if not is_admin and user_id:
                application = self.application_repo.find_by_id(application_id)
                if not application:
                    return False, "APPLICATION_NOT_FOUND", None

                application_obj = application
                if isinstance(application, dict):
                    from app.onlus.models.onlus_application import ONLUSApplication
                    application_obj = ONLUSApplication.from_dict(application)

                if user_id != application_obj.applicant_id:
                    return False, "DOCUMENTS_ACCESS_DENIED", None

            # Get documents
            documents = self.document_repo.find_by_application_id(application_id)

            documents_data = []
            for doc in documents:
                doc_data = doc.to_dict(include_sensitive=is_admin)

                # Add additional metadata
                doc_data['is_expired'] = doc.is_expired()
                doc_data['is_expiring_soon'] = doc.is_expiring_soon()
                doc_data['is_latest_version'] = self._is_latest_version(doc, documents)

                documents_data.append(doc_data)

            # Group by document type for easier consumption
            grouped_documents = {}
            for doc_data in documents_data:
                doc_type = doc_data['document_type']
                if doc_type not in grouped_documents:
                    grouped_documents[doc_type] = []
                grouped_documents[doc_type].append(doc_data)

            # Sort each group by version descending
            for doc_type in grouped_documents:
                grouped_documents[doc_type].sort(key=lambda x: x['version'], reverse=True)

            return True, "APPLICATION_DOCUMENTS_RETRIEVED_SUCCESS", {
                "application_id": application_id,
                "documents": documents_data,
                "grouped_by_type": grouped_documents,
                "total_documents": len(documents_data)
            }

        except Exception as e:
            current_app.logger.error(f"Failed to get application documents: {str(e)}")
            return False, "APPLICATION_DOCUMENTS_RETRIEVAL_FAILED", None

    def review_document(self, document_id: str, admin_id: str,
                       review_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict]]:
        """
        Review a document (approve, reject, or request resubmission).

        Args:
            document_id: Document ID
            admin_id: Admin reviewing the document
            review_data: Review decision and notes

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, review result
        """
        try:
            # Get document
            document_data = self.document_repo.find_by_id(document_id)
            if not document_data:
                return False, "DOCUMENT_NOT_FOUND", None

            document = ONLUSDocument.from_dict(document_data)

            # Check if document can be reviewed
            if document.status not in [DocumentStatus.PENDING.value, DocumentStatus.UNDER_REVIEW.value]:
                return False, "DOCUMENT_NOT_REVIEWABLE", None

            # Get review decision
            action = review_data.get('action')  # 'approve', 'reject', 'resubmit'
            notes = review_data.get('notes', '')

            if action == 'approve':
                document.approve_document(admin_id, notes)
                message = "DOCUMENT_APPROVED_SUCCESS"

            elif action == 'reject':
                rejection_reason = review_data.get('rejection_reason', '')
                if not rejection_reason:
                    return False, "REJECTION_REASON_REQUIRED", None

                document.reject_document(admin_id, rejection_reason, notes)
                message = "DOCUMENT_REJECTED_SUCCESS"

            elif action == 'resubmit':
                resubmission_reason = review_data.get('resubmission_reason', '')
                if not resubmission_reason:
                    return False, "RESUBMISSION_REASON_REQUIRED", None

                document.request_resubmission(admin_id, resubmission_reason)
                message = "DOCUMENT_RESUBMISSION_REQUESTED_SUCCESS"

            else:
                return False, "INVALID_REVIEW_ACTION", None

            # Save document updates
            success = self.document_repo.update_document(document_id, document)
            if not success:
                return False, "DOCUMENT_REVIEW_SAVE_FAILED", None

            # Update application progress
            self._update_application_progress(document.application_id)

            current_app.logger.info(f"Document reviewed: {document_id} by admin {admin_id} - action: {action}")

            return True, message, {
                "document_id": document_id,
                "action": action,
                "status": document.status,
                "reviewed_by": document.reviewed_by,
                "review_date": document.review_date
            }

        except Exception as e:
            current_app.logger.error(f"Failed to review document: {str(e)}")
            return False, "DOCUMENT_REVIEW_FAILED", None

    def get_documents_for_review(self, document_type: str = None,
                               limit: int = None) -> Tuple[bool, str, Optional[List[Dict]]]:
        """
        Get documents pending admin review.

        Args:
            document_type: Optional document type filter
            limit: Optional limit on number of documents

        Returns:
            Tuple[bool, str, Optional[List[Dict]]]: Success, message, documents list
        """
        try:
            # Get pending documents
            pending_documents = self.document_repo.get_pending_review_documents()

            # Filter by document type if specified
            if document_type:
                pending_documents = [doc for doc in pending_documents if doc.document_type == document_type]

            # Apply limit if specified
            if limit:
                pending_documents = pending_documents[:limit]

            documents_data = []
            for doc in pending_documents:
                doc_data = doc.to_dict(include_sensitive=True)

                # Add application info
                application = self.application_repo.find_by_id(doc.application_id)
                if application:
                    application_obj = application
                    if isinstance(application, dict):
                        from app.onlus.models.onlus_application import ONLUSApplication
                        application_obj = ONLUSApplication.from_dict(application)

                    doc_data['application_info'] = {
                        "organization_name": application_obj.organization_name,
                        "category": application_obj.category,
                        "status": application_obj.status,
                        "priority": application_obj.priority
                    }

                documents_data.append(doc_data)

            # Sort by priority and upload date
            documents_data.sort(key=lambda x: (
                x.get('application_info', {}).get('priority', 'normal'),
                x['upload_date']
            ))

            return True, "REVIEW_DOCUMENTS_RETRIEVED_SUCCESS", documents_data

        except Exception as e:
            current_app.logger.error(f"Failed to get documents for review: {str(e)}")
            return False, "REVIEW_DOCUMENTS_RETRIEVAL_FAILED", None

    def get_document_download_url(self, document_id: str, user_id: str = None,
                                is_admin: bool = False) -> Tuple[bool, str, Optional[str]]:
        """
        Get secure download URL for a document.

        Args:
            document_id: Document ID
            user_id: User ID (for authorization)
            is_admin: Whether user is admin

        Returns:
            Tuple[bool, str, Optional[str]]: Success, message, download URL
        """
        try:
            # Get document
            document_data = self.document_repo.find_by_id(document_id)
            if not document_data:
                return False, "DOCUMENT_NOT_FOUND", None

            document = ONLUSDocument.from_dict(document_data)

            # Check authorization if not admin
            if not is_admin and user_id:
                application = self.application_repo.find_by_id(document.application_id)
                if not application:
                    return False, "APPLICATION_NOT_FOUND", None

                application_obj = application
                if isinstance(application, dict):
                    from app.onlus.models.onlus_application import ONLUSApplication
                    application_obj = ONLUSApplication.from_dict(application)

                if user_id != application_obj.applicant_id:
                    return False, "DOCUMENT_ACCESS_DENIED", None

            # Generate secure download URL (implementation would depend on storage provider)
            # For now, return the file URL (in production, this would be a signed URL with expiration)
            download_url = document.file_url

            current_app.logger.info(f"Document download URL generated: {document_id}")

            return True, "DOCUMENT_DOWNLOAD_URL_GENERATED_SUCCESS", download_url

        except Exception as e:
            current_app.logger.error(f"Failed to generate download URL: {str(e)}")
            return False, "DOCUMENT_DOWNLOAD_URL_GENERATION_FAILED", None

    def delete_document(self, document_id: str, user_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Delete a document (only allowed for draft applications).

        Args:
            document_id: Document ID
            user_id: User ID (for authorization)

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, deletion result
        """
        try:
            # Get document
            document_data = self.document_repo.find_by_id(document_id)
            if not document_data:
                return False, "DOCUMENT_NOT_FOUND", None

            document = ONLUSDocument.from_dict(document_data)

            # Get application to check status and authorization
            application = self.application_repo.find_by_id(document.application_id)
            if not application:
                return False, "APPLICATION_NOT_FOUND", None

            application_obj = application
            if isinstance(application, dict):
                from app.onlus.models.onlus_application import ONLUSApplication
                application_obj = ONLUSApplication.from_dict(application)

            # Check authorization
            if user_id != application_obj.applicant_id:
                return False, "DOCUMENT_DELETE_ACCESS_DENIED", None

            # Check if document can be deleted
            if application_obj.status != ApplicationStatus.DRAFT.value:
                return False, "DOCUMENT_DELETE_NOT_ALLOWED", None

            if document.status not in [DocumentStatus.PENDING.value, DocumentStatus.REJECTED.value]:
                return False, "DOCUMENT_DELETE_STATUS_NOT_ALLOWED", None

            # Delete document from repository
            success = self.document_repo.delete_by_id(document_id)
            if not success:
                return False, "DOCUMENT_DELETION_FAILED", None

            # Remove from application documents list
            if document_id in application_obj.submitted_documents:
                application_obj.submitted_documents.remove(document_id)
                application_obj.calculate_completion_percentage()
                self.application_repo.update_application(document.application_id, application_obj)

            # TODO: Delete file from storage system

            current_app.logger.info(f"Document deleted: {document_id} by user {user_id}")

            return True, "DOCUMENT_DELETED_SUCCESS", {
                "document_id": document_id,
                "document_type": document.document_type
            }

        except Exception as e:
            current_app.logger.error(f"Failed to delete document: {str(e)}")
            return False, "DOCUMENT_DELETION_FAILED", None

    def get_document_statistics(self) -> Tuple[bool, str, Optional[Dict]]:
        """
        Get document management statistics.

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, statistics
        """
        try:
            # Get expired and expiring documents
            expired_docs = self.document_repo.get_expired_documents()
            expiring_docs = self.document_repo.get_expiring_documents()

            # Get documents by status
            pending_docs = self.document_repo.get_documents_by_status(DocumentStatus.PENDING.value)
            approved_docs = self.document_repo.get_documents_by_status(DocumentStatus.APPROVED.value)
            rejected_docs = self.document_repo.get_documents_by_status(DocumentStatus.REJECTED.value)

            statistics = {
                "total_documents": len(pending_docs) + len(approved_docs) + len(rejected_docs),
                "by_status": {
                    "pending": len(pending_docs),
                    "approved": len(approved_docs),
                    "rejected": len(rejected_docs)
                },
                "expired_count": len(expired_docs),
                "expiring_soon_count": len(expiring_docs),
                "documents_needing_attention": len(expired_docs) + len(expiring_docs) + len(pending_docs),
                "generated_at": datetime.now(timezone.utc)
            }

            return True, "DOCUMENT_STATISTICS_RETRIEVED_SUCCESS", statistics

        except Exception as e:
            current_app.logger.error(f"Failed to get document statistics: {str(e)}")
            return False, "DOCUMENT_STATISTICS_RETRIEVAL_FAILED", None

    def process_expired_documents(self) -> Tuple[bool, str, Optional[Dict]]:
        """
        Process expired documents (mark as expired, send notifications).

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, processing results
        """
        try:
            # Mark expired documents
            expired_count = self.document_repo.mark_documents_as_expired()

            # Get documents expiring soon for notifications
            expiring_docs = self.document_repo.get_expiring_documents(days=7)

            # TODO: Send notifications to affected applications

            current_app.logger.info(f"Processed expired documents: {expired_count} marked as expired, {len(expiring_docs)} expiring soon")

            return True, "EXPIRED_DOCUMENTS_PROCESSED_SUCCESS", {
                "expired_count": expired_count,
                "expiring_soon_count": len(expiring_docs),
                "processed_at": datetime.now(timezone.utc)
            }

        except Exception as e:
            current_app.logger.error(f"Failed to process expired documents: {str(e)}")
            return False, "EXPIRED_DOCUMENTS_PROCESSING_FAILED", None

    def _document_expires(self, document_type: str) -> bool:
        """Check if a document type has expiration."""
        expiring_types = [
            DocumentType.FINANCIAL_REPORT.value,
            DocumentType.INSURANCE_COVERAGE.value,
            DocumentType.COMPLIANCE_CERTIFICATE.value,
            DocumentType.TAX_EXEMPT_STATUS.value
        ]
        return document_type in expiring_types

    def _is_latest_version(self, document: ONLUSDocument, all_documents: List[ONLUSDocument]) -> bool:
        """Check if document is the latest version of its type."""
        same_type_docs = [doc for doc in all_documents
                         if doc.document_type == document.document_type
                         and doc.application_id == document.application_id]

        if not same_type_docs:
            return True

        max_version = max(doc.version for doc in same_type_docs)
        return document.version == max_version

    def _update_application_progress(self, application_id: str):
        """Update application progress after document status change."""
        try:
            application = self.application_repo.find_by_id(application_id)
            if application:
                application_obj = application
                if isinstance(application, dict):
                    from app.onlus.models.onlus_application import ONLUSApplication
                    application_obj = ONLUSApplication.from_dict(application)

                application_obj.calculate_completion_percentage()
                self.application_repo.update_application(application_id, application_obj)

        except Exception as e:
            current_app.logger.error(f"Failed to update application progress: {str(e)}")