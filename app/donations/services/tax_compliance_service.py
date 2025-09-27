from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from flask import current_app
from enum import Enum
from app.donations.repositories.transaction_repository import TransactionRepository
from app.core.repositories.user_repository import UserRepository


class TaxJurisdiction(Enum):
    """Tax jurisdictions supported by the platform."""
    ITALY = "IT"
    EUROPEAN_UNION = "EU"
    UNITED_STATES = "US"
    UNITED_KINGDOM = "UK"
    OTHER = "OTHER"


class TaxComplianceService:
    """
    Service for managing tax compliance and deductibility rules.

    Handles tax regulations, deductibility limits, documentation requirements,
    and compliance validation for different jurisdictions.
    """

    def __init__(self):
        self.transaction_repo = TransactionRepository()
        self.user_repo = UserRepository()

        # Tax compliance configuration by jurisdiction
        self.tax_rules = {
            TaxJurisdiction.ITALY: {
                'min_deductible_amount': 2.0,
                'max_annual_deductible': 30000.0,
                'max_income_percentage': 0.10,  # 10% of income
                'qualified_organization_types': ['ONLUS', 'ONG', 'NPO', 'RELIGIOUS'],
                'documentation_required': True,
                'receipt_retention_years': 7,
                'special_limits': {
                    'disaster_relief': 50000.0,
                    'research_institutions': 100000.0,
                    'cultural_heritage': 25000.0
                }
            },
            TaxJurisdiction.EUROPEAN_UNION: {
                'min_deductible_amount': 1.0,
                'max_annual_deductible': 20000.0,
                'max_income_percentage': 0.08,
                'qualified_organization_types': ['EU_QUALIFIED', 'CHARITY', 'NPO'],
                'documentation_required': True,
                'receipt_retention_years': 5,
                'special_limits': {}
            },
            TaxJurisdiction.UNITED_STATES: {
                'min_deductible_amount': 1.0,
                'max_annual_deductible': None,  # No federal limit
                'max_income_percentage': 0.60,  # 60% of AGI for qualified organizations
                'qualified_organization_types': ['501C3', 'RELIGIOUS', 'GOVERNMENT'],
                'documentation_required': True,
                'receipt_retention_years': 3,
                'special_limits': {
                    'cash_contributions': 0.60,  # 60% of AGI
                    'property_contributions': 0.30  # 30% of AGI
                }
            }
        }

    def validate_tax_deductibility(self, user_id: str, amount: float,
                                 onlus_id: str, jurisdiction: str = "IT") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Validate if a donation is tax deductible.

        Args:
            user_id: User identifier
            amount: Donation amount
            onlus_id: ONLUS organization identifier
            jurisdiction: Tax jurisdiction code

        Returns:
            Tuple[bool, str, Optional[Dict]]: Is deductible, message, validation details
        """
        try:
            # Get jurisdiction enum
            try:
                tax_jurisdiction = TaxJurisdiction(jurisdiction)
            except ValueError:
                tax_jurisdiction = TaxJurisdiction.OTHER

            # Get tax rules for jurisdiction
            rules = self.tax_rules.get(tax_jurisdiction)
            if not rules:
                return False, "TAX_JURISDICTION_NOT_SUPPORTED", None

            # Basic amount validation
            if amount < rules['min_deductible_amount']:
                return False, "AMOUNT_BELOW_MINIMUM_DEDUCTIBLE", {
                    'minimum_amount': rules['min_deductible_amount'],
                    'provided_amount': amount
                }

            # Check annual limit
            if rules['max_annual_deductible']:
                annual_donated = self._get_annual_donated_amount(user_id, datetime.now().year)
                if annual_donated + amount > rules['max_annual_deductible']:
                    return False, "ANNUAL_DEDUCTIBLE_LIMIT_EXCEEDED", {
                        'annual_limit': rules['max_annual_deductible'],
                        'current_annual_donated': annual_donated,
                        'requested_amount': amount,
                        'available_deductible': max(0, rules['max_annual_deductible'] - annual_donated)
                    }

            # Validate organization qualification
            org_validation = self._validate_organization_qualification(onlus_id, tax_jurisdiction)
            if not org_validation['is_qualified']:
                return False, "ORGANIZATION_NOT_TAX_QUALIFIED", org_validation

            # Calculate deductibility details
            deductibility_details = {
                'is_deductible': True,
                'jurisdiction': jurisdiction,
                'deductible_amount': amount,
                'tax_year': datetime.now().year,
                'organization_qualified': True,
                'documentation_required': rules['documentation_required'],
                'receipt_retention_years': rules['receipt_retention_years'],
                'validation_timestamp': datetime.now(timezone.utc),
                'rules_applied': {
                    'min_amount_check': f"€{amount:.2f} >= €{rules['min_deductible_amount']:.2f}",
                    'annual_limit_check': f"Within annual limit of €{rules['max_annual_deductible'] or 'No limit'}",
                    'organization_check': "Organization qualified for tax deductions"
                }
            }

            current_app.logger.info(f"Tax deductibility validated for user {user_id}: €{amount:.2f} is deductible")

            return True, "TAX_DEDUCTIBILITY_VALIDATED", deductibility_details

        except Exception as e:
            current_app.logger.error(f"Failed to validate tax deductibility: {str(e)}")
            return False, "TAX_VALIDATION_ERROR", None

    def _get_annual_donated_amount(self, user_id: str, tax_year: int) -> float:
        """
        Get total donated amount for a user in a tax year.

        Args:
            user_id: User identifier
            tax_year: Tax year

        Returns:
            Total donated amount
        """
        try:
            # Get user's donation transactions for the tax year
            start_date = datetime(tax_year, 1, 1, tzinfo=timezone.utc)
            end_date = datetime(tax_year + 1, 1, 1, tzinfo=timezone.utc)

            transactions = self.transaction_repo.find_transactions_by_date_range(
                user_id=user_id,
                transaction_type="donated",
                start_date=start_date,
                end_date=end_date
            )

            return sum(t.amount for t in transactions if t.amount > 0)

        except Exception as e:
            current_app.logger.error(f"Failed to get annual donated amount for {user_id}: {str(e)}")
            return 0.0

    def _validate_organization_qualification(self, onlus_id: str,
                                          jurisdiction: TaxJurisdiction) -> Dict[str, Any]:
        """
        Validate if an organization is qualified for tax deductions.

        Args:
            onlus_id: ONLUS organization identifier
            jurisdiction: Tax jurisdiction

        Returns:
            Validation result dictionary
        """
        try:
            # For now, return placeholder validation
            # In production, this would check against official databases

            # Get organization details (placeholder)
            org_details = {
                'onlus_id': onlus_id,
                'organization_type': 'ONLUS',  # Placeholder
                'tax_id': f"IT{onlus_id}",  # Placeholder
                'qualification_status': 'ACTIVE',
                'qualification_expiry': datetime(2025, 12, 31),
                'supported_jurisdictions': [TaxJurisdiction.ITALY, TaxJurisdiction.EUROPEAN_UNION]
            }

            # Check if organization supports this jurisdiction
            is_qualified = jurisdiction in org_details['supported_jurisdictions']

            # Check qualification status
            if org_details['qualification_status'] != 'ACTIVE':
                is_qualified = False

            # Check qualification expiry
            if org_details['qualification_expiry'] < datetime.now():
                is_qualified = False

            return {
                'is_qualified': is_qualified,
                'organization_details': org_details,
                'qualification_reason': "Active qualified organization" if is_qualified else "Organization not qualified",
                'validation_date': datetime.now(timezone.utc)
            }

        except Exception as e:
            current_app.logger.error(f"Failed to validate organization qualification: {str(e)}")
            return {
                'is_qualified': False,
                'organization_details': None,
                'qualification_reason': "Validation error",
                'validation_date': datetime.now(timezone.utc)
            }

    def calculate_tax_benefit(self, user_id: str, donation_amount: float,
                            user_income: float = None, jurisdiction: str = "IT") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Calculate potential tax benefit from a donation.

        Args:
            user_id: User identifier
            donation_amount: Donation amount
            user_income: User's annual income (if available)
            jurisdiction: Tax jurisdiction code

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, tax benefit details
        """
        try:
            # Validate deductibility first
            is_deductible, message, validation_details = self.validate_tax_deductibility(
                user_id, donation_amount, "default_onlus", jurisdiction
            )

            if not is_deductible:
                return False, message, validation_details

            # Get jurisdiction rules
            try:
                tax_jurisdiction = TaxJurisdiction(jurisdiction)
            except ValueError:
                tax_jurisdiction = TaxJurisdiction.OTHER

            rules = self.tax_rules.get(tax_jurisdiction)
            if not rules:
                return False, "TAX_JURISDICTION_NOT_SUPPORTED", None

            # Calculate tax benefit based on jurisdiction
            if tax_jurisdiction == TaxJurisdiction.ITALY:
                tax_benefit = self._calculate_italy_tax_benefit(donation_amount, user_income)
            elif tax_jurisdiction == TaxJurisdiction.UNITED_STATES:
                tax_benefit = self._calculate_us_tax_benefit(donation_amount, user_income)
            elif tax_jurisdiction == TaxJurisdiction.EUROPEAN_UNION:
                tax_benefit = self._calculate_eu_tax_benefit(donation_amount, user_income)
            else:
                tax_benefit = {
                    'estimated_deduction': donation_amount,
                    'estimated_tax_savings': donation_amount * 0.20,  # 20% estimate
                    'calculation_method': 'generic_estimate'
                }

            tax_benefit.update({
                'donation_amount': donation_amount,
                'jurisdiction': jurisdiction,
                'calculation_date': datetime.now(timezone.utc),
                'disclaimer': "Tax benefit calculations are estimates. Consult a tax professional for accurate advice."
            })

            return True, "TAX_BENEFIT_CALCULATED", tax_benefit

        except Exception as e:
            current_app.logger.error(f"Failed to calculate tax benefit: {str(e)}")
            return False, "TAX_BENEFIT_CALCULATION_ERROR", None

    def _calculate_italy_tax_benefit(self, donation_amount: float,
                                   user_income: float = None) -> Dict[str, Any]:
        """
        Calculate tax benefit for Italy tax system.

        Italy allows deduction of 26% of donation amount up to certain limits.
        """
        # Italian tax deduction: 26% of donation amount
        tax_deduction_rate = 0.26
        estimated_tax_savings = donation_amount * tax_deduction_rate

        return {
            'estimated_deduction': donation_amount,
            'estimated_tax_savings': estimated_tax_savings,
            'tax_deduction_rate': tax_deduction_rate,
            'calculation_method': 'italy_deduction_26_percent',
            'notes': "26% tax deduction on donation amount, subject to annual limits"
        }

    def _calculate_us_tax_benefit(self, donation_amount: float,
                                user_income: float = None) -> Dict[str, Any]:
        """
        Calculate tax benefit for US tax system.

        US allows itemized deduction up to 60% of AGI for cash donations.
        """
        # Estimate marginal tax rate (would need user's actual tax bracket)
        estimated_marginal_rate = 0.22  # 22% bracket estimate
        estimated_tax_savings = donation_amount * estimated_marginal_rate

        return {
            'estimated_deduction': donation_amount,
            'estimated_tax_savings': estimated_tax_savings,
            'estimated_marginal_rate': estimated_marginal_rate,
            'calculation_method': 'us_itemized_deduction',
            'notes': "Itemized deduction, subject to AGI limits and other tax considerations"
        }

    def _calculate_eu_tax_benefit(self, donation_amount: float,
                                user_income: float = None) -> Dict[str, Any]:
        """
        Calculate tax benefit for EU tax systems (generic).

        EU member states have varying rules, this provides a general estimate.
        """
        # Generic EU estimate: 20% tax relief
        estimated_tax_relief_rate = 0.20
        estimated_tax_savings = donation_amount * estimated_tax_relief_rate

        return {
            'estimated_deduction': donation_amount,
            'estimated_tax_savings': estimated_tax_savings,
            'tax_relief_rate': estimated_tax_relief_rate,
            'calculation_method': 'eu_generic_estimate',
            'notes': "Generic EU estimate. Actual benefits vary by member state."
        }

    def get_tax_documentation_requirements(self, jurisdiction: str = "IT") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get tax documentation requirements for a jurisdiction.

        Args:
            jurisdiction: Tax jurisdiction code

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, requirements
        """
        try:
            # Get jurisdiction enum
            try:
                tax_jurisdiction = TaxJurisdiction(jurisdiction)
            except ValueError:
                tax_jurisdiction = TaxJurisdiction.OTHER

            # Get tax rules
            rules = self.tax_rules.get(tax_jurisdiction)
            if not rules:
                return False, "TAX_JURISDICTION_NOT_SUPPORTED", None

            requirements = {
                'jurisdiction': jurisdiction,
                'documentation_required': rules['documentation_required'],
                'receipt_retention_years': rules['receipt_retention_years'],
                'min_amount_for_receipt': rules['min_deductible_amount'],
                'qualified_organizations': rules['qualified_organization_types'],
                'annual_limits': {
                    'max_deductible': rules['max_annual_deductible'],
                    'max_income_percentage': rules['max_income_percentage']
                },
                'special_limits': rules.get('special_limits', {}),
                'requirements_details': self._get_detailed_requirements(tax_jurisdiction)
            }

            return True, "TAX_REQUIREMENTS_RETRIEVED", requirements

        except Exception as e:
            current_app.logger.error(f"Failed to get tax documentation requirements: {str(e)}")
            return False, "TAX_REQUIREMENTS_ERROR", None

    def _get_detailed_requirements(self, jurisdiction: TaxJurisdiction) -> Dict[str, Any]:
        """
        Get detailed tax requirements for a jurisdiction.

        Args:
            jurisdiction: Tax jurisdiction enum

        Returns:
            Detailed requirements dictionary
        """
        if jurisdiction == TaxJurisdiction.ITALY:
            return {
                'receipt_requirements': [
                    "Official receipt from qualified ONLUS organization",
                    "Donor name and tax identification number",
                    "Organization tax identification number",
                    "Donation amount and date",
                    "Statement of tax-exempt purpose"
                ],
                'filing_requirements': [
                    "Include donation details in annual tax return",
                    "Attach receipts if requested by tax authority",
                    "Keep records for 7 years after filing"
                ],
                'special_rules': [
                    "26% tax deduction on donation amount",
                    "Maximum €30,000 annual deduction",
                    "Must be made to qualified Italian organizations"
                ]
            }
        elif jurisdiction == TaxJurisdiction.UNITED_STATES:
            return {
                'receipt_requirements': [
                    "Written acknowledgment from 501(c)(3) organization",
                    "Donor name and tax identification number",
                    "Organization's EIN (tax ID number)",
                    "Donation amount and date",
                    "Statement that no goods or services were provided"
                ],
                'filing_requirements': [
                    "Itemize deductions on Schedule A",
                    "Attach Form 8283 for non-cash donations over $500",
                    "Keep records for 3 years after filing"
                ],
                'special_rules': [
                    "Deductions limited to 60% of AGI for cash donations",
                    "Different limits apply for different organization types",
                    "Excess donations can be carried forward up to 5 years"
                ]
            }
        else:
            return {
                'receipt_requirements': [
                    "Official receipt from qualified organization",
                    "Donor identification information",
                    "Organization identification",
                    "Donation details and date"
                ],
                'filing_requirements': [
                    "Include in annual tax filing as required by local law",
                    "Retain documentation as required by jurisdiction"
                ],
                'special_rules': [
                    "Rules vary by jurisdiction",
                    "Consult local tax advisor for specific requirements"
                ]
            }

    def get_annual_tax_summary(self, user_id: str, tax_year: int) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Get annual tax summary for a user.

        Args:
            user_id: User identifier
            tax_year: Tax year

        Returns:
            Tuple[bool, str, Optional[Dict]]: Success, message, tax summary
        """
        try:
            # Get user's donations for the tax year
            annual_donated = self._get_annual_donated_amount(user_id, tax_year)

            if annual_donated == 0:
                return False, "NO_DONATIONS_IN_TAX_YEAR", None

            # Get detailed transactions
            start_date = datetime(tax_year, 1, 1, tzinfo=timezone.utc)
            end_date = datetime(tax_year + 1, 1, 1, tzinfo=timezone.utc)

            transactions = self.transaction_repo.find_transactions_by_date_range(
                user_id=user_id,
                transaction_type="donated",
                start_date=start_date,
                end_date=end_date
            )

            # Calculate tax deductible amount
            tax_deductible_amount = 0
            for transaction in transactions:
                # Check if each donation is tax deductible
                is_deductible, _, _ = self.validate_tax_deductibility(
                    user_id, transaction.amount,
                    transaction.metadata.get('onlus_id', 'default'),
                    "IT"
                )
                if is_deductible:
                    tax_deductible_amount += transaction.amount

            # Calculate estimated tax benefit
            success, _, tax_benefit = self.calculate_tax_benefit(
                user_id, tax_deductible_amount, jurisdiction="IT"
            )

            tax_summary = {
                'user_id': user_id,
                'tax_year': tax_year,
                'total_donated': annual_donated,
                'tax_deductible_amount': tax_deductible_amount,
                'non_deductible_amount': annual_donated - tax_deductible_amount,
                'donation_count': len(transactions),
                'estimated_tax_savings': tax_benefit.get('estimated_tax_savings', 0) if success else 0,
                'generated_at': datetime.now(timezone.utc),
                'transactions': [
                    {
                        'transaction_id': t.transaction_id,
                        'amount': float(t.amount),
                        'date': t.created_at.isoformat() if t.created_at else None,
                        'onlus_name': t.metadata.get('onlus_name', 'Unknown'),
                        'is_tax_deductible': self.validate_tax_deductibility(
                            user_id, t.amount,
                            t.metadata.get('onlus_id', 'default'),
                            "IT"
                        )[0]
                    }
                    for t in transactions
                ]
            }

            return True, "ANNUAL_TAX_SUMMARY_GENERATED", tax_summary

        except Exception as e:
            current_app.logger.error(f"Failed to generate annual tax summary: {str(e)}")
            return False, "ANNUAL_TAX_SUMMARY_ERROR", None