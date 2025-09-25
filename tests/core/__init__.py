"""
GoodPlay Test Core Module

This module provides the foundational architecture for the GoodPlay test suite,
including configuration management, base test classes, and utilities.

Components:
- TestConfig: Centralized test configuration management
- TestBase: Base class for all test cases
- Utils: Common testing utilities and helpers
- Interfaces: Abstract test interfaces for consistent testing patterns
"""

from .config import TestConfig
from .test_base import TestBase
from .utils import TestUtils

__all__ = [
    'TestConfig',
    'TestBase',
    'TestUtils'
]