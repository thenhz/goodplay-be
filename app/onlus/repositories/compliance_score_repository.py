from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from app.core.database import get_db
from app.core.repositories.base_repository import BaseRepository
from app.onlus.models.compliance_score import ComplianceScore, ComplianceLevel, ComplianceCategory, RiskLevel
import os


class ComplianceScoreRepository(BaseRepository[ComplianceScore]):
    """Repository for managing compliance score data operations."""

    def __init__(self):
        super().__init__()
        self.collection_name = 'compliance_scores'

    def create_indexes(self):
        """Create database indexes for compliance scores."""
        if self.collection is None or os.getenv('TESTING') == 'true':
            return

        try:
            self.collection.create_index([("onlus_id", 1), ("assessment_date", -1)])
            self.collection.create_index([("overall_score", -1)])
            self.collection.create_index([("compliance_level", 1)])
            self.collection.create_index([("risk_level", 1)])
            self.collection.create_index([("is_current", 1), ("onlus_id", 1)])
            self.collection.create_index([("next_assessment_due", 1)])
            self.collection.create_index([("is_verified", 1)])
            self.collection.create_index([("assessment_period_start", 1), ("assessment_period_end", 1)])
        except Exception:
            pass

    def create_score(self, score: ComplianceScore) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Create a new compliance score."""
        try:
            # Mark previous scores as non-current for this ONLUS
            self.collection.update_many(
                {"onlus_id": score.onlus_id, "is_current": True},
                {"$set": {"is_current": False, "updated_at": datetime.now(timezone.utc)}}
            )

            score_dict = score.to_dict()
            score_dict.pop('_id', None)

            result = self.collection.insert_one(score_dict)
            score._id = result.inserted_id

            return True, "COMPLIANCE_SCORE_CREATED_SUCCESS", score.to_dict()
        except Exception as e:
            return False, "COMPLIANCE_SCORE_CREATION_FAILED", None

    def get_score_by_id(self, score_id: str) -> Tuple[bool, str, Optional[ComplianceScore]]:
        """Get compliance score by ID."""
        try:
            score_data = self.collection.find_one({"_id": ObjectId(score_id)})
            if score_data:
                score = ComplianceScore.from_dict(score_data)
                return True, "COMPLIANCE_SCORE_RETRIEVED_SUCCESS", score
            return False, "COMPLIANCE_SCORE_NOT_FOUND", None
        except Exception as e:
            return False, "COMPLIANCE_SCORE_RETRIEVAL_FAILED", None

    def get_current_score_by_onlus(self, onlus_id: str) -> Tuple[bool, str, Optional[ComplianceScore]]:
        """Get current compliance score for an ONLUS."""
        try:
            score_data = self.collection.find_one({
                "onlus_id": onlus_id,
                "is_current": True
            })
            if score_data:
                score = ComplianceScore.from_dict(score_data)
                return True, "CURRENT_COMPLIANCE_SCORE_SUCCESS", score
            return False, "COMPLIANCE_SCORE_NOT_FOUND", None
        except Exception as e:
            return False, "CURRENT_COMPLIANCE_SCORE_FAILED", None

    def get_scores_by_onlus(self, onlus_id: str, limit: int = 50,
                           skip: int = 0) -> Tuple[bool, str, Optional[List[ComplianceScore]]]:
        """Get compliance score history for an ONLUS."""
        try:
            cursor = (self.collection.find({"onlus_id": onlus_id})
                     .sort([("assessment_date", -1)])
                     .skip(skip).limit(limit))

            scores = [ComplianceScore.from_dict(doc) for doc in cursor]
            return True, "ONLUS_COMPLIANCE_SCORES_SUCCESS", scores
        except Exception as e:
            return False, "ONLUS_COMPLIANCE_SCORES_FAILED", None

    def get_scores_by_compliance_level(self, compliance_level: str,
                                     current_only: bool = True,
                                     limit: int = 100) -> Tuple[bool, str, Optional[List[ComplianceScore]]]:
        """Get scores by compliance level."""
        try:
            query = {"compliance_level": compliance_level}
            if current_only:
                query["is_current"] = True

            cursor = (self.collection.find(query)
                     .sort([("overall_score", -1)])
                     .limit(limit))

            scores = [ComplianceScore.from_dict(doc) for doc in cursor]
            return True, "COMPLIANCE_LEVEL_SCORES_SUCCESS", scores
        except Exception as e:
            return False, "COMPLIANCE_LEVEL_SCORES_FAILED", None

    def get_scores_by_risk_level(self, risk_level: str,
                                current_only: bool = True,
                                limit: int = 100) -> Tuple[bool, str, Optional[List[ComplianceScore]]]:
        """Get scores by risk level."""
        try:
            query = {"risk_level": risk_level}
            if current_only:
                query["is_current"] = True

            cursor = (self.collection.find(query)
                     .sort([("overall_score", 1)])  # Low scores first for high risk
                     .limit(limit))

            scores = [ComplianceScore.from_dict(doc) for doc in cursor]
            return True, "RISK_LEVEL_SCORES_SUCCESS", scores
        except Exception as e:
            return False, "RISK_LEVEL_SCORES_FAILED", None

    def get_scores_needing_assessment(self, days_overdue: int = 0) -> Tuple[bool, str, Optional[List[ComplianceScore]]]:
        """Get scores that need reassessment."""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_overdue)
            query = {
                "is_current": True,
                "$or": [
                    {"next_assessment_due": {"$lte": cutoff_date}},
                    {"next_assessment_due": None}
                ]
            }

            cursor = (self.collection.find(query)
                     .sort([("next_assessment_due", 1)])
                     .limit(50))

            scores = [ComplianceScore.from_dict(doc) for doc in cursor]
            return True, "ASSESSMENT_DUE_SCORES_SUCCESS", scores
        except Exception as e:
            return False, "ASSESSMENT_DUE_SCORES_FAILED", None

    def get_high_risk_scores(self, current_only: bool = True,
                           limit: int = 50) -> Tuple[bool, str, Optional[List[ComplianceScore]]]:
        """Get high-risk compliance scores."""
        try:
            query = {
                "risk_level": {"$in": [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]}
            }
            if current_only:
                query["is_current"] = True

            cursor = (self.collection.find(query)
                     .sort([("overall_score", 1), ("open_issues_count", -1)])
                     .limit(limit))

            scores = [ComplianceScore.from_dict(doc) for doc in cursor]
            return True, "HIGH_RISK_SCORES_SUCCESS", scores
        except Exception as e:
            return False, "HIGH_RISK_SCORES_FAILED", None

    def get_scores_with_critical_issues(self, current_only: bool = True) -> Tuple[bool, str, Optional[List[ComplianceScore]]]:
        """Get scores with critical compliance issues."""
        try:
            query = {
                "compliance_issues": {
                    "$elemMatch": {
                        "severity": "critical",
                        "status": "open"
                    }
                }
            }
            if current_only:
                query["is_current"] = True

            cursor = (self.collection.find(query)
                     .sort([("critical_issues_count", -1), ("overall_score", 1)])
                     .limit(100))

            scores = [ComplianceScore.from_dict(doc) for doc in cursor]
            return True, "CRITICAL_ISSUES_SCORES_SUCCESS", scores
        except Exception as e:
            return False, "CRITICAL_ISSUES_SCORES_FAILED", None

    def get_top_performing_scores(self, limit: int = 20,
                                 current_only: bool = True) -> Tuple[bool, str, Optional[List[ComplianceScore]]]:
        """Get top performing compliance scores."""
        try:
            query = {}
            if current_only:
                query["is_current"] = True

            cursor = (self.collection.find(query)
                     .sort([("overall_score", -1)])
                     .limit(limit))

            scores = [ComplianceScore.from_dict(doc) for doc in cursor]
            return True, "TOP_PERFORMING_SCORES_SUCCESS", scores
        except Exception as e:
            return False, "TOP_PERFORMING_SCORES_FAILED", None

    def update_score(self, score: ComplianceScore) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Update compliance score."""
        try:
            score.updated_at = datetime.now(timezone.utc)
            score_dict = score.to_dict()
            score_id = score_dict.pop('_id')

            self.collection.update_one(
                {"_id": score_id},
                {"$set": score_dict}
            )

            return True, "COMPLIANCE_SCORE_UPDATED_SUCCESS", score.to_dict()
        except Exception as e:
            return False, "COMPLIANCE_SCORE_UPDATE_FAILED", None

    def update_category_score(self, score_id: str, category: str,
                             new_score: float) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Update a specific category score."""
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(score_id)},
                {
                    "$set": {
                        f"category_scores.{category}": float(new_score),
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )

            if result.matched_count:
                # Recalculate overall score
                score_data = self.collection.find_one({"_id": ObjectId(score_id)})
                if score_data:
                    score = ComplianceScore.from_dict(score_data)
                    score.calculate_overall_score()
                    self.update_score(score)

                return True, "CATEGORY_SCORE_UPDATED_SUCCESS", {category: new_score}
            return False, "COMPLIANCE_SCORE_NOT_FOUND", None
        except Exception as e:
            return False, "CATEGORY_SCORE_UPDATE_FAILED", None

    def add_compliance_issue(self, score_id: str, issue_type: str,
                           description: str, severity: str = "medium",
                           category: str = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Add a compliance issue to a score."""
        try:
            issue = {
                'issue_id': str(ObjectId()),
                'issue_type': issue_type,
                'description': description,
                'severity': severity,
                'category': category,
                'identified_at': datetime.now(timezone.utc),
                'status': 'open'
            }

            result = self.collection.update_one(
                {"_id": ObjectId(score_id)},
                {
                    "$push": {"compliance_issues": issue},
                    "$set": {"updated_at": datetime.now(timezone.utc)}
                }
            )

            if result.matched_count:
                # Update risk level based on new issue
                score_data = self.collection.find_one({"_id": ObjectId(score_id)})
                if score_data:
                    score = ComplianceScore.from_dict(score_data)
                    score.update_risk_level()
                    self.update_score(score)

                return True, "COMPLIANCE_ISSUE_ADDED_SUCCESS", issue
            return False, "COMPLIANCE_SCORE_NOT_FOUND", None
        except Exception as e:
            return False, "COMPLIANCE_ISSUE_ADD_FAILED", None

    def resolve_compliance_issue(self, score_id: str, issue_id: str,
                               resolution_notes: str = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Resolve a compliance issue."""
        try:
            result = self.collection.update_one(
                {
                    "_id": ObjectId(score_id),
                    "compliance_issues.issue_id": issue_id
                },
                {
                    "$set": {
                        "compliance_issues.$.status": "resolved",
                        "compliance_issues.$.resolved_at": datetime.now(timezone.utc),
                        "compliance_issues.$.resolution_notes": resolution_notes,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )

            if result.matched_count:
                # Update risk level after resolving issue
                score_data = self.collection.find_one({"_id": ObjectId(score_id)})
                if score_data:
                    score = ComplianceScore.from_dict(score_data)
                    score.update_risk_level()
                    self.update_score(score)

                return True, "COMPLIANCE_ISSUE_RESOLVED_SUCCESS", {"issue_id": issue_id}
            return False, "COMPLIANCE_ISSUE_NOT_FOUND", None
        except Exception as e:
            return False, "COMPLIANCE_ISSUE_RESOLVE_FAILED", None

    def add_monitoring_alert(self, score_id: str, alert_type: str,
                           message: str, urgency: str = "medium") -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Add a monitoring alert to a score."""
        try:
            alert = {
                'alert_id': str(ObjectId()),
                'alert_type': alert_type,
                'message': message,
                'urgency': urgency,
                'triggered_at': datetime.now(timezone.utc),
                'status': 'active'
            }

            result = self.collection.update_one(
                {"_id": ObjectId(score_id)},
                {
                    "$push": {"monitoring_alerts": alert},
                    "$set": {"updated_at": datetime.now(timezone.utc)}
                }
            )

            if result.matched_count:
                return True, "MONITORING_ALERT_ADDED_SUCCESS", alert
            return False, "COMPLIANCE_SCORE_NOT_FOUND", None
        except Exception as e:
            return False, "MONITORING_ALERT_ADD_FAILED", None

    def dismiss_monitoring_alert(self, score_id: str, alert_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Dismiss a monitoring alert."""
        try:
            result = self.collection.update_one(
                {
                    "_id": ObjectId(score_id),
                    "monitoring_alerts.alert_id": alert_id
                },
                {
                    "$set": {
                        "monitoring_alerts.$.status": "dismissed",
                        "monitoring_alerts.$.dismissed_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )

            if result.matched_count:
                return True, "MONITORING_ALERT_DISMISSED_SUCCESS", {"alert_id": alert_id}
            return False, "MONITORING_ALERT_NOT_FOUND", None
        except Exception as e:
            return False, "MONITORING_ALERT_DISMISS_FAILED", None

    def set_benchmark_comparison(self, score_id: str, metric: str,
                               organization_value: float, peer_average: float,
                               percentile: int) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Set benchmark comparison data."""
        try:
            benchmark_data = {
                'organization_value': float(organization_value),
                'peer_average': float(peer_average),
                'percentile': int(percentile),
                'performance': 'above_average' if organization_value > peer_average else 'below_average',
                'updated_at': datetime.now(timezone.utc)
            }

            result = self.collection.update_one(
                {"_id": ObjectId(score_id)},
                {
                    "$set": {
                        f"benchmark_comparisons.{metric}": benchmark_data,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )

            if result.matched_count:
                return True, "BENCHMARK_SET_SUCCESS", {metric: benchmark_data}
            return False, "COMPLIANCE_SCORE_NOT_FOUND", None
        except Exception as e:
            return False, "BENCHMARK_SET_FAILED", None

    def verify_assessment(self, score_id: str, verifier_id: str,
                         verification_notes: str = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Verify a compliance assessment."""
        try:
            verification_details = {
                'verifier_id': verifier_id,
                'verified_at': datetime.now(timezone.utc),
                'verification_notes': verification_notes
            }

            result = self.collection.update_one(
                {"_id": ObjectId(score_id)},
                {
                    "$set": {
                        "is_verified": True,
                        "verification_details": verification_details,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )

            if result.matched_count:
                return True, "ASSESSMENT_VERIFIED_SUCCESS", verification_details
            return False, "COMPLIANCE_SCORE_NOT_FOUND", None
        except Exception as e:
            return False, "ASSESSMENT_VERIFICATION_FAILED", None

    def get_compliance_statistics(self, start_date: datetime = None,
                                 end_date: datetime = None,
                                 current_only: bool = True) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Get compliance statistics."""
        try:
            match_stage = {}
            if current_only:
                match_stage["is_current"] = True

            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter["$gte"] = start_date
                if end_date:
                    date_filter["$lte"] = end_date
                match_stage["assessment_date"] = date_filter

            pipeline = [
                {"$match": match_stage},
                {
                    "$group": {
                        "_id": None,
                        "total_assessments": {"$sum": 1},
                        "avg_overall_score": {"$avg": "$overall_score"},
                        "excellent_count": {
                            "$sum": {"$cond": [{"$eq": ["$compliance_level", "excellent"]}, 1, 0]}
                        },
                        "good_count": {
                            "$sum": {"$cond": [{"$eq": ["$compliance_level", "good"]}, 1, 0]}
                        },
                        "satisfactory_count": {
                            "$sum": {"$cond": [{"$eq": ["$compliance_level", "satisfactory"]}, 1, 0]}
                        },
                        "needs_attention_count": {
                            "$sum": {"$cond": [{"$eq": ["$compliance_level", "needs_attention"]}, 1, 0]}
                        },
                        "critical_count": {
                            "$sum": {"$cond": [{"$eq": ["$compliance_level", "critical"]}, 1, 0]}
                        },
                        "low_risk_count": {
                            "$sum": {"$cond": [{"$eq": ["$risk_level", "low"]}, 1, 0]}
                        },
                        "moderate_risk_count": {
                            "$sum": {"$cond": [{"$eq": ["$risk_level", "moderate"]}, 1, 0]}
                        },
                        "high_risk_count": {
                            "$sum": {"$cond": [{"$eq": ["$risk_level", "high"]}, 1, 0]}
                        },
                        "critical_risk_count": {
                            "$sum": {"$cond": [{"$eq": ["$risk_level", "critical"]}, 1, 0]}
                        },
                        "verified_assessments": {
                            "$sum": {"$cond": ["$is_verified", 1, 0]}
                        },
                        "avg_open_issues": {"$avg": "$open_issues_count"},
                        "avg_critical_issues": {"$avg": "$critical_issues_count"}
                    }
                }
            ]

            result = list(self.collection.aggregate(pipeline))
            if result:
                stats = result[0]
                stats.pop('_id', None)

                # Calculate percentages
                total = stats.get('total_assessments', 0)
                if total > 0:
                    stats['excellent_percentage'] = stats.get('excellent_count', 0) / total * 100
                    stats['verification_rate'] = stats.get('verified_assessments', 0) / total * 100
                    stats['high_risk_percentage'] = (stats.get('high_risk_count', 0) + stats.get('critical_risk_count', 0)) / total * 100

                return True, "COMPLIANCE_STATISTICS_SUCCESS", stats
            else:
                return True, "COMPLIANCE_STATISTICS_SUCCESS", {
                    "total_assessments": 0,
                    "avg_overall_score": 0,
                    "excellent_count": 0,
                    "good_count": 0,
                    "satisfactory_count": 0,
                    "needs_attention_count": 0,
                    "critical_count": 0,
                    "low_risk_count": 0,
                    "moderate_risk_count": 0,
                    "high_risk_count": 0,
                    "critical_risk_count": 0,
                    "verified_assessments": 0,
                    "avg_open_issues": 0,
                    "avg_critical_issues": 0,
                    "excellent_percentage": 0,
                    "verification_rate": 0,
                    "high_risk_percentage": 0
                }
        except Exception as e:
            return False, "COMPLIANCE_STATISTICS_FAILED", None

    def get_compliance_trends(self, onlus_id: str = None,
                            months: int = 12) -> Tuple[bool, str, Optional[List[Dict[str, Any]]]]:
        """Get compliance score trends over time."""
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=months * 30)

            match_stage = {"assessment_date": {"$gte": start_date}}
            if onlus_id:
                match_stage["onlus_id"] = onlus_id

            pipeline = [
                {"$match": match_stage},
                {
                    "$group": {
                        "_id": {
                            "year": {"$year": "$assessment_date"},
                            "month": {"$month": "$assessment_date"}
                        },
                        "avg_score": {"$avg": "$overall_score"},
                        "assessment_count": {"$sum": 1},
                        "avg_risk_score": {"$avg": {
                            "$switch": {
                                "branches": [
                                    {"case": {"$eq": ["$risk_level", "low"]}, "then": 1},
                                    {"case": {"$eq": ["$risk_level", "moderate"]}, "then": 2},
                                    {"case": {"$eq": ["$risk_level", "high"]}, "then": 3},
                                    {"case": {"$eq": ["$risk_level", "critical"]}, "then": 4}
                                ],
                                "default": 2
                            }
                        }}
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "date": {
                            "$dateFromParts": {
                                "year": "$_id.year",
                                "month": "$_id.month"
                            }
                        },
                        "avg_score": {"$round": ["$avg_score", 2]},
                        "assessment_count": 1,
                        "avg_risk_score": {"$round": ["$avg_risk_score", 2]}
                    }
                },
                {"$sort": {"date": 1}}
            ]

            trends = list(self.collection.aggregate(pipeline))
            return True, "COMPLIANCE_TRENDS_SUCCESS", trends
        except Exception as e:
            return False, "COMPLIANCE_TRENDS_FAILED", None

    def delete_score(self, score_id: str) -> Tuple[bool, str, None]:
        """Delete compliance score (hard delete)."""
        try:
            result = self.collection.delete_one({"_id": ObjectId(score_id)})

            if result.deleted_count:
                return True, "COMPLIANCE_SCORE_DELETED_SUCCESS", None
            return False, "COMPLIANCE_SCORE_NOT_FOUND", None
        except Exception as e:
            return False, "COMPLIANCE_SCORE_DELETE_FAILED", None