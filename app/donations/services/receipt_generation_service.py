from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from flask import current_app
import os
import uuid
from app.donations.repositories.transaction_repository import TransactionRepository
from app.donations.repositories.wallet_repository import WalletRepository
from app.core.repositories.user_repository import UserRepository


class ReceiptGenerationService:
    """
    Service for generating donation receipts and tax documentation.

    Handles PDF receipt generation, tax deductibility calculations,
    receipt storage, and email delivery for donation transparency.
    """

    def __init__(self):
        self.transaction_repo = TransactionRepository()
        self.wallet_repo = WalletRepository()
        self.user_repo = UserRepository()

        # Receipt configuration
        self.receipt_template_path = "templates/receipts/"
        self.receipt_storage_path = "receipts/"
        self.max_receipt_age_days = 365 * 7  # 7 years for tax purposes

    def generate_donation_receipt(self, transaction_id: str,
                                 receipt_type: str = "standard") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Generate a donation receipt for a transaction.

        Args:
            transaction_id: Transaction identifier
            receipt_type: Type of receipt (standard, tax_deductible, annual_summary)

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, receipt data
        """
        try:
            # Get transaction details
            transaction = self.transaction_repo.find_by_transaction_id(transaction_id)
            if not transaction:
                return False, "TRANSACTION_NOT_FOUND", None

            if transaction.transaction_type != "donated":
                return False, "TRANSACTION_NOT_DONATION", None

            # Get user details
            user = self.user_repo.find_user_by_id(transaction.user_id)
            if not user:
                return False, "USER_NOT_FOUND", None

            # Generate receipt data
            receipt_data = self._prepare_receipt_data(transaction, user, receipt_type)

            # Generate PDF receipt
            pdf_success, pdf_message, pdf_info = self._generate_pdf_receipt(receipt_data)
            if not pdf_success:
                return False, pdf_message, None

            # Store receipt metadata
            receipt_metadata = {
                'receipt_id': receipt_data['receipt_id'],
                'transaction_id': transaction_id,
                'user_id': transaction.user_id,
                'receipt_type': receipt_type,
                'pdf_path': pdf_info['pdf_path'],
                'pdf_size_bytes': pdf_info['pdf_size'],
                'generated_at': datetime.now(timezone.utc),
                'tax_year': receipt_data['tax_year'],
                'is_tax_deductible': receipt_data['is_tax_deductible'],
                'donation_amount': receipt_data['donation_amount'],
                'onlus_id': receipt_data['onlus_id']
            }

            # Save receipt record
            success = self._save_receipt_metadata(receipt_metadata)
            if not success:
                current_app.logger.warning(f"Failed to save receipt metadata for {receipt_data['receipt_id']}")

            current_app.logger.info(f"Generated receipt {receipt_data['receipt_id']} for transaction {transaction_id}")

            return True, "RECEIPT_GENERATED_SUCCESS", {
                'receipt_id': receipt_data['receipt_id'],
                'pdf_path': pdf_info['pdf_path'],
                'receipt_type': receipt_type,
                'is_tax_deductible': receipt_data['is_tax_deductible'],
                'tax_year': receipt_data['tax_year'],
                'download_url': f"/api/donations/{transaction_id}/receipt/download"
            }

        except Exception as e:
            current_app.logger.error(f"Failed to generate receipt for transaction {transaction_id}: {str(e)}")
            return False, "RECEIPT_GENERATION_ERROR", None

    def _prepare_receipt_data(self, transaction, user, receipt_type: str) -> Dict[str, Any]:
        """
        Prepare data for receipt generation.

        Args:
            transaction: Transaction object
            user: User object
            receipt_type: Type of receipt

        Returns:
            Receipt data dictionary
        """
        receipt_id = f"RCP-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        tax_year = transaction.created_at.year if transaction.created_at else datetime.now().year

        # Calculate tax deductibility
        is_tax_deductible = self._is_donation_tax_deductible(transaction.amount, transaction.metadata)

        return {
            'receipt_id': receipt_id,
            'transaction_id': transaction.transaction_id,
            'user_id': transaction.user_id,
            'user_name': f"{user.first_name} {user.last_name}",
            'user_email': user.email,
            'donation_amount': float(transaction.amount),
            'donation_currency': 'EUR',
            'donation_date': transaction.created_at.strftime('%Y-%m-%d') if transaction.created_at else None,
            'onlus_id': transaction.metadata.get('onlus_id'),
            'onlus_name': transaction.metadata.get('onlus_name', 'ONLUS Organization'),
            'donation_message': transaction.metadata.get('message', ''),
            'is_anonymous': transaction.metadata.get('is_anonymous', False),
            'tax_year': tax_year,
            'is_tax_deductible': is_tax_deductible,
            'receipt_type': receipt_type,
            'generated_at': datetime.now(timezone.utc),
            'platform_name': 'GoodPlay',
            'platform_address': 'Via Example 123, 00100 Roma, Italy',
            'platform_tax_id': 'IT12345678901',  # Placeholder
            'receipt_note': self._get_receipt_note(receipt_type, is_tax_deductible)
        }

    def _is_donation_tax_deductible(self, amount: float, metadata: Dict[str, Any]) -> bool:
        """
        Determine if a donation is tax deductible.

        Args:
            amount: Donation amount
            metadata: Transaction metadata

        Returns:
            True if tax deductible
        """
        # Basic tax deductibility rules for Italy
        # Minimum deductible amount: €2
        if amount < 2.0:
            return False

        # Maximum annual deductible: €30,000 or 10% of income
        # This would need user income data for full validation
        if amount > 30000:
            return False

        # Check if ONLUS is qualified for tax deductions
        onlus_qualified = metadata.get('onlus_tax_qualified', True)  # Default to qualified

        return onlus_qualified

    def _get_receipt_note(self, receipt_type: str, is_tax_deductible: bool) -> str:
        """
        Get appropriate note for receipt type.

        Args:
            receipt_type: Type of receipt
            is_tax_deductible: Whether donation is tax deductible

        Returns:
            Receipt note text
        """
        if receipt_type == "tax_deductible" and is_tax_deductible:
            return ("This receipt serves as proof of your tax-deductible donation. "
                   "Keep this document for your tax records. Consult your tax advisor "
                   "for specific deduction eligibility and limits.")
        elif receipt_type == "annual_summary":
            return ("This is your annual donation summary for tax purposes. "
                   "Individual transaction receipts are available separately.")
        else:
            return ("Thank you for your generous donation. This receipt confirms "
                   "your contribution to our platform's charitable activities.")

    def _generate_pdf_receipt(self, receipt_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Generate PDF receipt from data.

        Args:
            receipt_data: Receipt data dictionary

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, PDF info
        """
        try:
            # For now, return a placeholder implementation
            # In production, this would use ReportLab or WeasyPrint

            # Create receipts directory if it doesn't exist
            os.makedirs(self.receipt_storage_path, exist_ok=True)

            # Generate PDF filename
            receipt_id = receipt_data['receipt_id']
            pdf_filename = f"{receipt_id}.pdf"
            pdf_path = os.path.join(self.receipt_storage_path, pdf_filename)

            # Placeholder PDF content
            pdf_content = self._generate_placeholder_pdf_content(receipt_data)

            # Write PDF file (placeholder)
            with open(pdf_path, 'w') as f:
                f.write(pdf_content)

            # Get file size
            pdf_size = os.path.getsize(pdf_path)

            current_app.logger.info(f"Generated PDF receipt at {pdf_path}")

            return True, "PDF_GENERATED_SUCCESS", {
                'pdf_path': pdf_path,
                'pdf_filename': pdf_filename,
                'pdf_size': pdf_size
            }

        except Exception as e:
            current_app.logger.error(f"Failed to generate PDF receipt: {str(e)}")
            return False, "PDF_GENERATION_ERROR", None

    def _generate_placeholder_pdf_content(self, receipt_data: Dict[str, Any]) -> str:
        """
        Generate placeholder PDF content (text format).

        In production, this would use proper PDF generation libraries.
        """
        return f"""
DONATION RECEIPT
================

Receipt ID: {receipt_data['receipt_id']}
Date Generated: {receipt_data['generated_at'].strftime('%Y-%m-%d %H:%M')}

DONOR INFORMATION
-----------------
Name: {receipt_data['user_name']}
Email: {receipt_data['user_email']}

DONATION DETAILS
----------------
Amount: €{receipt_data['donation_amount']:.2f}
Date: {receipt_data['donation_date']}
Organization: {receipt_data['onlus_name']}
Message: {receipt_data['donation_message']}

TAX INFORMATION
---------------
Tax Year: {receipt_data['tax_year']}
Tax Deductible: {'Yes' if receipt_data['is_tax_deductible'] else 'No'}

PLATFORM INFORMATION
--------------------
Platform: {receipt_data['platform_name']}
Address: {receipt_data['platform_address']}
Tax ID: {receipt_data['platform_tax_id']}

NOTE
----
{receipt_data['receipt_note']}

This is a computer-generated receipt and does not require a signature.
For questions, please contact our support team.
"""

    def _save_receipt_metadata(self, receipt_metadata: Dict[str, Any]) -> bool:
        """
        Save receipt metadata to database.

        Args:
            receipt_metadata: Receipt metadata dictionary

        Returns:
            True if saved successfully
        """
        try:
            # For now, just log the receipt metadata
            # In production, this would save to a receipts collection
            current_app.logger.info(f"Receipt metadata: {receipt_metadata['receipt_id']}")
            return True

        except Exception as e:
            current_app.logger.error(f"Failed to save receipt metadata: {str(e)}")
            return False

    def get_user_receipts(self, user_id: str, tax_year: int = None) -> Tuple[bool, str, Optional[List[Dict[str, Any]]]]:
        """
        Get all receipts for a user.

        Args:
            user_id: User identifier
            tax_year: Optional filter by tax year

        Returns:
            Tuple[bool, str, Optional[List]]: Success, message, receipts list
        """
        try:
            # Get user's donation transactions
            transactions = self.transaction_repo.find_user_transactions(
                user_id=user_id,
                transaction_type="donated",
                limit=1000  # Large limit for receipt history
            )

            if not transactions:
                return True, "NO_RECEIPTS_FOUND", []

            # Filter by tax year if specified
            if tax_year:
                transactions = [t for t in transactions
                               if t.created_at and t.created_at.year == tax_year]

            # Build receipts list
            receipts = []
            for transaction in transactions:
                receipt_info = {
                    'transaction_id': transaction.transaction_id,
                    'amount': float(transaction.amount),
                    'date': transaction.created_at.strftime('%Y-%m-%d') if transaction.created_at else None,
                    'onlus_name': transaction.metadata.get('onlus_name', 'ONLUS Organization'),
                    'tax_year': transaction.created_at.year if transaction.created_at else datetime.now().year,
                    'is_tax_deductible': self._is_donation_tax_deductible(transaction.amount, transaction.metadata),
                    'receipt_available': True,
                    'download_url': f"/api/donations/{transaction.transaction_id}/receipt/download"
                }
                receipts.append(receipt_info)

            return True, "RECEIPTS_RETRIEVED", receipts

        except Exception as e:
            current_app.logger.error(f"Failed to get user receipts for {user_id}: {str(e)}")
            return False, "RECEIPTS_RETRIEVAL_ERROR", None

    def generate_annual_summary(self, user_id: str, tax_year: int) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Generate annual donation summary for tax purposes.

        Args:
            user_id: User identifier
            tax_year: Tax year for summary

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, summary data
        """
        try:
            # Get user's donations for the tax year
            success, message, receipts = self.get_user_receipts(user_id, tax_year)
            if not success:
                return False, message, None

            if not receipts:
                return False, "NO_DONATIONS_IN_TAX_YEAR", None

            # Calculate summary statistics
            total_donations = sum(r['amount'] for r in receipts)
            tax_deductible_donations = sum(r['amount'] for r in receipts if r['is_tax_deductible'])
            donation_count = len(receipts)
            tax_deductible_count = sum(1 for r in receipts if r['is_tax_deductible'])

            # Get user details
            user = self.user_repo.find_user_by_id(user_id)
            if not user:
                return False, "USER_NOT_FOUND", None

            # Prepare annual summary data
            summary_data = {
                'user_id': user_id,
                'user_name': f"{user.first_name} {user.last_name}",
                'user_email': user.email,
                'tax_year': tax_year,
                'total_donations': total_donations,
                'tax_deductible_donations': tax_deductible_donations,
                'donation_count': donation_count,
                'tax_deductible_count': tax_deductible_count,
                'receipts': receipts,
                'generated_at': datetime.now(timezone.utc),
                'summary_id': f"ANNUAL-{tax_year}-{user_id[:8].upper()}"
            }

            # Generate summary PDF
            pdf_success, pdf_message, pdf_info = self._generate_annual_summary_pdf(summary_data)
            if pdf_success:
                summary_data['pdf_path'] = pdf_info['pdf_path']
                summary_data['download_url'] = f"/api/donations/annual-summary/{tax_year}/download"

            current_app.logger.info(f"Generated annual summary for user {user_id}, year {tax_year}")

            return True, "ANNUAL_SUMMARY_GENERATED", summary_data

        except Exception as e:
            current_app.logger.error(f"Failed to generate annual summary for {user_id}: {str(e)}")
            return False, "ANNUAL_SUMMARY_ERROR", None

    def _generate_annual_summary_pdf(self, summary_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Generate PDF for annual donation summary.

        Args:
            summary_data: Annual summary data

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, PDF info
        """
        try:
            # Generate PDF filename
            summary_id = summary_data['summary_id']
            pdf_filename = f"{summary_id}.pdf"
            pdf_path = os.path.join(self.receipt_storage_path, pdf_filename)

            # Generate placeholder PDF content
            pdf_content = f"""
ANNUAL DONATION SUMMARY
=====================

Summary ID: {summary_id}
Tax Year: {summary_data['tax_year']}
Generated: {summary_data['generated_at'].strftime('%Y-%m-%d %H:%M')}

DONOR INFORMATION
-----------------
Name: {summary_data['user_name']}
Email: {summary_data['user_email']}

DONATION SUMMARY
----------------
Total Donations: €{summary_data['total_donations']:.2f}
Total Transactions: {summary_data['donation_count']}
Tax Deductible Donations: €{summary_data['tax_deductible_donations']:.2f}
Tax Deductible Transactions: {summary_data['tax_deductible_count']}

INDIVIDUAL DONATIONS
-------------------
"""
            for receipt in summary_data['receipts']:
                pdf_content += f"""
Date: {receipt['date']}
Organization: {receipt['onlus_name']}
Amount: €{receipt['amount']:.2f}
Tax Deductible: {'Yes' if receipt['is_tax_deductible'] else 'No'}
---
"""

            pdf_content += """

This summary is for tax purposes only. Keep this document with your tax records.
Consult your tax advisor for specific deduction eligibility and limits.
"""

            # Write PDF file (placeholder)
            with open(pdf_path, 'w') as f:
                f.write(pdf_content)

            pdf_size = os.path.getsize(pdf_path)

            return True, "ANNUAL_SUMMARY_PDF_GENERATED", {
                'pdf_path': pdf_path,
                'pdf_filename': pdf_filename,
                'pdf_size': pdf_size
            }

        except Exception as e:
            current_app.logger.error(f"Failed to generate annual summary PDF: {str(e)}")
            return False, "ANNUAL_SUMMARY_PDF_ERROR", None

    def cleanup_old_receipts(self, retention_days: int = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Clean up old receipt files to save storage space.

        Args:
            retention_days: Days to retain receipts (default: max_receipt_age_days)

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, cleanup stats
        """
        try:
            retention_days = retention_days or self.max_receipt_age_days
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

            # For now, just return placeholder stats
            # In production, this would scan and delete old receipt files
            cleanup_stats = {
                'files_checked': 0,
                'files_deleted': 0,
                'storage_freed_bytes': 0,
                'cutoff_date': cutoff_date.isoformat(),
                'retention_days': retention_days
            }

            current_app.logger.info(f"Receipt cleanup completed: {cleanup_stats}")

            return True, "RECEIPT_CLEANUP_COMPLETED", cleanup_stats

        except Exception as e:
            current_app.logger.error(f"Failed to cleanup old receipts: {str(e)}")
            return False, "RECEIPT_CLEANUP_ERROR", None