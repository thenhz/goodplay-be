#!/usr/bin/env python3
"""
Test Pattern Analysis Script for GOO-35 Migration

Automatically analyzes existing test files to identify patterns, boilerplate,
and opportunities for migration to GOO-35 Testing Utilities.

Usage:
    python tests/migration/analyze_patterns.py
    python tests/migration/analyze_patterns.py --file tests/test_core_auth.py
    python tests/migration/analyze_patterns.py --category core --report detailed
"""

import os
import ast
import re
import argparse
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict
import json


@dataclass
class TestAnalysisResult:
    """Analysis result for a single test file"""
    file_path: str
    total_lines: int
    test_methods: int
    fixture_count: int
    mock_count: int
    boilerplate_lines: int
    setup_methods: int
    teardown_methods: int
    import_statements: int
    patterns: List[str] = field(default_factory=list)
    migration_opportunities: List[str] = field(default_factory=list)
    recommended_base_class: str = 'BaseUnitTest'
    estimated_reduction: float = 0.0


@dataclass
class MigrationRecommendation:
    """Migration recommendation for a test file"""
    current_pattern: str
    recommended_pattern: str
    benefit: str
    example_before: str
    example_after: str
    effort_level: str  # 'low', 'medium', 'high'


class TestPatternAnalyzer:
    """Analyzes test files to identify migration opportunities"""

    def __init__(self):
        self.patterns = {
            'pytest_fixture': re.compile(r'@pytest\.fixture'),
            'unittest_setup': re.compile(r'def setUp\(self\)'),
            'unittest_teardown': re.compile(r'def tearDown\(self\)'),
            'mock_patch': re.compile(r'@patch\('),
            'mock_creation': re.compile(r'Mock\(|MagicMock\('),
            'manual_data_creation': re.compile(r'{\s*[\'"].*[\'"]\s*:\s*.*}'),
            'assert_statements': re.compile(r'assert\s+'),
            'service_injection': re.compile(r'service\s*=\s*\w+Service\('),
            'repository_mocking': re.compile(r'mock_.*repository'),
            'auth_headers': re.compile(r'[\'"]Authorization[\'"].*Bearer'),
            'jwt_mocking': re.compile(r'create_access_token|create_refresh_token'),
            'database_mocking': re.compile(r'mock_db|MagicMock.*collection'),
            'test_data_dicts': re.compile(r'test_\w+\s*=\s*{'),
        }

        self.base_class_indicators = {
            'BaseAuthTest': ['auth', 'login', 'jwt', 'token', 'password', 'bcrypt'],
            'BaseGameTest': ['game', 'plugin', 'session', 'score', 'multiplayer'],
            'BaseSocialTest': ['friend', 'achievement', 'leaderboard', 'team', 'social'],
            'BasePreferencesTest': ['preferences', 'settings', 'config', 'privacy'],
            'BaseServiceTest': ['service', 'business_logic', 'validation'],
            'BaseControllerTest': ['controller', 'endpoint', 'api', 'route'],
            'BaseIntegrationTest': ['integration', 'end_to_end', 'workflow']
        }

    def analyze_file(self, file_path: str) -> TestAnalysisResult:
        """Analyze a single test file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse AST for detailed analysis
            tree = ast.parse(content)

            result = TestAnalysisResult(
                file_path=file_path,
                total_lines=len(content.split('\n')),
                test_methods=self._count_test_methods(tree),
                fixture_count=self._count_fixtures(content),
                mock_count=self._count_mocks(content),
                boilerplate_lines=self._count_boilerplate_lines(content),
                setup_methods=self._count_setup_methods(tree),
                teardown_methods=self._count_teardown_methods(tree),
                import_statements=self._count_imports(tree)
            )

            # Analyze patterns
            result.patterns = self._identify_patterns(content)
            result.migration_opportunities = self._identify_migration_opportunities(content, result)
            result.recommended_base_class = self._recommend_base_class(file_path, content)
            result.estimated_reduction = self._estimate_boilerplate_reduction(result)

            return result

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return TestAnalysisResult(
                file_path=file_path,
                total_lines=0,
                test_methods=0,
                fixture_count=0,
                mock_count=0,
                boilerplate_lines=0,
                setup_methods=0,
                teardown_methods=0,
                import_statements=0
            )

    def _count_test_methods(self, tree: ast.AST) -> int:
        """Count test methods in AST"""
        count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                count += 1
        return count

    def _count_fixtures(self, content: str) -> int:
        """Count pytest fixtures"""
        return len(self.patterns['pytest_fixture'].findall(content))

    def _count_mocks(self, content: str) -> int:
        """Count mock usage"""
        patch_count = len(self.patterns['mock_patch'].findall(content))
        mock_count = len(self.patterns['mock_creation'].findall(content))
        return patch_count + mock_count

    def _count_boilerplate_lines(self, content: str) -> int:
        """Estimate boilerplate lines"""
        boilerplate_patterns = [
            r'def setUp\(self\):',
            r'def tearDown\(self\):',
            r'@pytest\.fixture',
            r'@patch\(',
            r'Mock\(|MagicMock\(',
            r'mock_\w+\s*=\s*Mock',
            r'self\.mock_\w+\.\w+\.return_value',
            r'with patch\(',
            r'assert isinstance\(',
            r'assert \w+ is not None',
            r'assert \w+ is None',
            r'assert len\(',
        ]

        boilerplate_count = 0
        lines = content.split('\n')

        for line in lines:
            line = line.strip()
            for pattern in boilerplate_patterns:
                if re.search(pattern, line):
                    boilerplate_count += 1
                    break

        return boilerplate_count

    def _count_setup_methods(self, tree: ast.AST) -> int:
        """Count setup methods"""
        count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in ['setUp', 'setup_method', 'setup']:
                count += 1
        return count

    def _count_teardown_methods(self, tree: ast.AST) -> int:
        """Count teardown methods"""
        count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in ['tearDown', 'teardown_method', 'teardown']:
                count += 1
        return count

    def _count_imports(self, tree: ast.AST) -> int:
        """Count import statements"""
        count = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                count += 1
        return count

    def _identify_patterns(self, content: str) -> List[str]:
        """Identify common test patterns"""
        identified = []

        for pattern_name, pattern_regex in self.patterns.items():
            if pattern_regex.search(content):
                identified.append(pattern_name)

        # Additional pattern detection
        if 'class Test' in content and 'unittest.TestCase' in content:
            identified.append('unittest_class')
        elif 'class Test' in content:
            identified.append('pytest_class')

        if 'BaseTest' in content or 'Base' in content and 'Test' in content:
            identified.append('existing_base_class')

        return identified

    def _identify_migration_opportunities(self, content: str, result: TestAnalysisResult) -> List[str]:
        """Identify specific migration opportunities"""
        opportunities = []

        # Check for manual mock setup
        if result.mock_count > 5:
            opportunities.append("High mock usage - candidate for BaseTest auto-injection")

        # Check for repetitive setup
        if result.setup_methods > 0 and result.fixture_count > 3:
            opportunities.append("Complex setup - candidate for BaseTest zero-setup pattern")

        # Check for manual data creation
        if self.patterns['test_data_dicts'].findall(content):
            opportunities.append("Manual test data creation - candidate for fluent builders")

        # Check for auth-related patterns
        if any(pattern in content.lower() for pattern in ['auth', 'login', 'jwt', 'token']):
            opportunities.append("Authentication testing - candidate for BaseAuthTest")

        # Check for game-related patterns
        if any(pattern in content.lower() for pattern in ['game', 'session', 'plugin', 'score']):
            opportunities.append("Game testing - candidate for BaseGameTest")

        # Check for social patterns
        if any(pattern in content.lower() for pattern in ['friend', 'achievement', 'social', 'team']):
            opportunities.append("Social features - candidate for BaseSocialTest")

        # Check for preference patterns
        if any(pattern in content.lower() for pattern in ['preference', 'setting', 'config']):
            opportunities.append("Preferences testing - candidate for BasePreferencesTest")

        # Check for assertion patterns
        assert_count = len(self.patterns['assert_statements'].findall(content))
        if assert_count > 10:
            opportunities.append("High assertion count - candidate for domain-specific assertions")

        return opportunities

    def _recommend_base_class(self, file_path: str, content: str) -> str:
        """Recommend appropriate base class"""
        file_name = os.path.basename(file_path).lower()
        content_lower = content.lower()

        # Score each base class based on indicators
        scores = defaultdict(int)

        for base_class, indicators in self.base_class_indicators.items():
            for indicator in indicators:
                if indicator in file_name or indicator in content_lower:
                    scores[base_class] += 1

        # Return highest scoring base class
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]

        # Default recommendations based on file name patterns
        if 'auth' in file_name:
            return 'BaseAuthTest'
        elif 'game' in file_name:
            return 'BaseGameTest'
        elif 'social' in file_name:
            return 'BaseSocialTest'
        elif 'preference' in file_name:
            return 'BasePreferencesTest'
        elif 'controller' in file_name or 'api' in file_name:
            return 'BaseControllerTest'
        elif 'integration' in file_name:
            return 'BaseIntegrationTest'
        elif 'service' in file_name:
            return 'BaseServiceTest'

        return 'BaseUnitTest'

    def _estimate_boilerplate_reduction(self, result: TestAnalysisResult) -> float:
        """Estimate potential boilerplate reduction percentage"""
        if result.total_lines == 0:
            return 0.0

        # Calculate reduction factors
        setup_reduction = min(result.setup_methods * 15, 50)  # Max 50 lines saved from setup
        fixture_reduction = min(result.fixture_count * 8, 40)  # Max 40 lines from fixtures
        mock_reduction = min(result.mock_count * 3, 30)       # Max 30 lines from mocks
        assertion_reduction = min(result.boilerplate_lines * 0.3, 20)  # Max 20% of boilerplate

        total_potential_reduction = setup_reduction + fixture_reduction + mock_reduction + assertion_reduction
        reduction_percentage = min(total_potential_reduction / result.total_lines * 100, 85)

        return round(reduction_percentage, 1)

    def analyze_directory(self, directory: str, pattern: str = "test_*.py") -> Dict[str, TestAnalysisResult]:
        """Analyze all test files in a directory"""
        results = {}
        test_dir = Path(directory)

        for test_file in test_dir.glob(pattern):
            if test_file.is_file():
                results[str(test_file)] = self.analyze_file(str(test_file))

        return results

    def generate_migration_recommendations(self, results: Dict[str, TestAnalysisResult]) -> List[MigrationRecommendation]:
        """Generate specific migration recommendations"""
        recommendations = []

        for file_path, result in results.items():
            base_name = os.path.basename(file_path)

            # High boilerplate reduction opportunity
            if result.estimated_reduction > 70:
                recommendations.append(MigrationRecommendation(
                    current_pattern="Manual setup/teardown with extensive mocking",
                    recommended_pattern=f"{result.recommended_base_class} with auto-injection",
                    benefit=f"Reduce {result.estimated_reduction}% of boilerplate",
                    example_before=f"setUp() with {result.mock_count} manual mocks",
                    example_after="Zero-setup with automatic dependency injection",
                    effort_level="medium"
                ))

            # Auth-specific recommendations
            if 'auth' in result.patterns or 'BaseAuthTest' in result.recommended_base_class:
                recommendations.append(MigrationRecommendation(
                    current_pattern="Manual JWT and bcrypt mocking",
                    recommended_pattern="BaseAuthTest with built-in auth utilities",
                    benefit="Standardized auth testing patterns",
                    example_before="Manual bcrypt.checkpw and JWT token mocking",
                    example_after="Built-in mock_successful_login() and assert_auth_response()",
                    effort_level="low"
                ))

            # Data creation recommendations
            if 'manual_data_creation' in result.patterns:
                recommendations.append(MigrationRecommendation(
                    current_pattern="Manual dictionary creation for test data",
                    recommended_pattern="Fluent builders with Factory-Boy integration",
                    benefit="Maintainable and readable test data creation",
                    example_before="user_data = {'email': '...', 'name': '...', ...}",
                    example_after="user_data = user().as_admin().with_email('...').build()",
                    effort_level="low"
                ))

        return recommendations


class MigrationReportGenerator:
    """Generates detailed migration reports"""

    def __init__(self, analyzer: TestPatternAnalyzer):
        self.analyzer = analyzer

    def generate_summary_report(self, results: Dict[str, TestAnalysisResult]) -> str:
        """Generate summary migration report"""
        total_files = len(results)
        total_lines = sum(r.total_lines for r in results.values())
        total_test_methods = sum(r.test_methods for r in results.values())
        total_fixtures = sum(r.fixture_count for r in results.values())
        total_mocks = sum(r.mock_count for r in results.values())
        total_boilerplate = sum(r.boilerplate_lines for r in results.values())

        avg_reduction = sum(r.estimated_reduction for r in results.values()) / total_files if total_files > 0 else 0

        report = f"""
# GOO-35 Migration Analysis Report

## Summary Statistics
- **Total test files analyzed**: {total_files}
- **Total lines of code**: {total_lines:,}
- **Total test methods**: {total_test_methods}
- **Total fixtures**: {total_fixtures}
- **Total mocks**: {total_mocks}
- **Boilerplate lines**: {total_boilerplate} ({total_boilerplate/total_lines*100:.1f}% of total)

## Migration Potential
- **Average estimated boilerplate reduction**: {avg_reduction:.1f}%
- **Total lines potentially saved**: {int(total_lines * avg_reduction / 100):,}

## File Analysis Results
"""

        # Sort by reduction potential
        sorted_results = sorted(results.items(), key=lambda x: x[1].estimated_reduction, reverse=True)

        for file_path, result in sorted_results:
            file_name = os.path.basename(file_path)
            report += f"""
### {file_name}
- **Lines**: {result.total_lines} | **Test methods**: {result.test_methods}
- **Fixtures**: {result.fixture_count} | **Mocks**: {result.mock_count} | **Boilerplate**: {result.boilerplate_lines}
- **Recommended base class**: {result.recommended_base_class}
- **Estimated reduction**: {result.estimated_reduction}%
- **Migration opportunities**: {len(result.migration_opportunities)}
  {chr(10).join(f'  - {opp}' for opp in result.migration_opportunities)}
"""

        return report

    def generate_detailed_report(self, results: Dict[str, TestAnalysisResult]) -> str:
        """Generate detailed migration report with recommendations"""
        summary = self.generate_summary_report(results)
        recommendations = self.analyzer.generate_migration_recommendations(results)

        detailed = summary + f"""

## Migration Recommendations ({len(recommendations)} items)

"""

        for i, rec in enumerate(recommendations, 1):
            detailed += f"""
### Recommendation {i}: {rec.current_pattern}
- **Replace with**: {rec.recommended_pattern}
- **Benefit**: {rec.benefit}
- **Effort level**: {rec.effort_level.title()}
- **Example transformation**:
  - Before: `{rec.example_before}`
  - After: `{rec.example_after}`

"""

        # Add base class recommendations
        base_class_counts = defaultdict(int)
        for result in results.values():
            base_class_counts[result.recommended_base_class] += 1

        detailed += """
## Recommended Base Class Distribution

"""
        for base_class, count in sorted(base_class_counts.items(), key=lambda x: x[1], reverse=True):
            detailed += f"- **{base_class}**: {count} files\n"

        return detailed

    def generate_json_report(self, results: Dict[str, TestAnalysisResult]) -> Dict[str, Any]:
        """Generate JSON report for programmatic use"""
        return {
            "summary": {
                "total_files": len(results),
                "total_lines": sum(r.total_lines for r in results.values()),
                "total_test_methods": sum(r.test_methods for r in results.values()),
                "average_reduction": sum(r.estimated_reduction for r in results.values()) / len(results) if results else 0
            },
            "files": {
                path: {
                    "total_lines": result.total_lines,
                    "test_methods": result.test_methods,
                    "fixture_count": result.fixture_count,
                    "mock_count": result.mock_count,
                    "boilerplate_lines": result.boilerplate_lines,
                    "estimated_reduction": result.estimated_reduction,
                    "recommended_base_class": result.recommended_base_class,
                    "patterns": result.patterns,
                    "migration_opportunities": result.migration_opportunities
                }
                for path, result in results.items()
            },
            "recommendations": [
                {
                    "current_pattern": rec.current_pattern,
                    "recommended_pattern": rec.recommended_pattern,
                    "benefit": rec.benefit,
                    "effort_level": rec.effort_level
                }
                for rec in self.analyzer.generate_migration_recommendations(results)
            ]
        }


def main():
    """Main entry point for the analysis script"""
    parser = argparse.ArgumentParser(description='Analyze test patterns for GOO-35 migration')
    parser.add_argument('--file', type=str, help='Analyze specific test file')
    parser.add_argument('--directory', type=str, default='tests', help='Directory to analyze (default: tests)')
    parser.add_argument('--pattern', type=str, default='test_*.py', help='File pattern to match (default: test_*.py)')
    parser.add_argument('--report', type=str, choices=['summary', 'detailed', 'json'], default='summary',
                       help='Report type (default: summary)')
    parser.add_argument('--output', type=str, help='Output file (default: stdout)')
    parser.add_argument('--category', type=str, choices=['core', 'games', 'social', 'preferences'],
                       help='Analyze specific category')

    args = parser.parse_args()

    analyzer = TestPatternAnalyzer()
    report_generator = MigrationReportGenerator(analyzer)

    # Determine what to analyze
    if args.file:
        results = {args.file: analyzer.analyze_file(args.file)}
    elif args.category:
        # Analyze category-specific files
        category_patterns = {
            'core': 'test_core_*.py',
            'games': 'test_game*.py',
            'social': 'test_social*.py',
            'preferences': 'test_preference*.py'
        }
        pattern = category_patterns.get(args.category, args.pattern)
        results = analyzer.analyze_directory(args.directory, pattern)
    else:
        results = analyzer.analyze_directory(args.directory, args.pattern)

    # Generate report
    if args.report == 'summary':
        report = report_generator.generate_summary_report(results)
    elif args.report == 'detailed':
        report = report_generator.generate_detailed_report(results)
    elif args.report == 'json':
        report = json.dumps(report_generator.generate_json_report(results), indent=2)

    # Output report
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Report written to {args.output}")
    else:
        print(report)


if __name__ == '__main__':
    main()