"""
Legacy TestBase compatibility module for backward compatibility

This module provides the TestBase class referenced by legacy test files
during the GOO-35 migration process.
"""
import unittest
from unittest.mock import MagicMock, patch


class TestBase(unittest.TestCase):
    """
    Legacy base test class for compatibility

    This class provides basic functionality for legacy tests
    while they are being migrated to GOO-35 architecture.
    """

    def setUp(self):
        """Basic setup for legacy tests"""
        super().setUp()
        self.mock_db = MagicMock()

    def tearDown(self):
        """Basic teardown for legacy tests"""
        super().tearDown()

    def create_test_data(self, **kwargs):
        """Create basic test data structure"""
        return {
            '_id': 'test_id',
            'created_at': '2024-01-01T00:00:00Z',
            **kwargs
        }