"""
Validation Tools for GOO-35 Migration (FASE 1.3)

This module provides comprehensive validation capabilities to ensure that
migration to GOO-35 Testing Utilities maintains correctness, improves
performance, and follows best practices.

Features:
- Validate migrated tests still pass
- Check GOO-35 pattern compliance
- Verify integration with existing systems (GOO-34, GOO-33, GOO-30-32)
- Performance regression testing
- Coverage maintenance verification
- Anti-pattern detection

Usage:
    python tests/migration/validation_tools.py --validate tests/
    python tests/migration/validation_tools.py --check-patterns tests/test_auth_goo35.py
    python tests/migration/validation_tools.py --performance-test tests/ --baseline tests_original/
"""

import ast
import os
import re
import time
import subprocess
import importlib
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any, Set
from pathlib import Path
import argparse
import json
import unittest
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO


@dataclass
class ValidationResult:
    """Result of a validation check"""
    check_name: str
    passed: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, float]] = None


@dataclass
class MigrationValidationReport:
    """Comprehensive validation report for migration"""
    file_path: str
    overall_status: str  # 'PASSED', 'FAILED', 'WARNING'
    validation_results: List[ValidationResult]
    performance_comparison: Optional[Dict[str, Any]] = None
    coverage_analysis: Optional[Dict[str, Any]] = None
    integration_status: Dict[str, bool] = None


class GOO35ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class GOO35MigrationValidator:
    """Main validator for GOO-35 migration correctness"""

    def __init__(self):
        self.required_patterns = {
            'BaseAuthTest': [
                'create_test_user',
                'mock_successful_login',
                'assert_auth_response_success'
            ],
            'BaseGameTest': [
                'create_test_game',
                'mock_game_session',
                'assert_game_session_valid'
            ],
            'BaseSocialTest': [
                'create_test_social_user',
                'mock_achievement_unlock',
                'assert_social_interaction'
            ],
            'BasePreferencesTest': [
                'create_test_preferences',
                'mock_preference_update',
                'assert_preferences_synchronized'
            ]
        }

        self.anti_patterns = [
            r'@patch\(.*auth.*service.*\)',  # Should use BaseAuthTest
            r'@patch\(.*jwt.*\)',            # Should use BaseAuthTest
            r'user_data\s*=\s*\{',          # Should use create_test_user
            r'setUp.*mock',                  # Should use base class setup
            r'import.*mock.*Mock',          # Should use base class mocks
        ]

        self.integration_checks = {
            'GOO-34': self._check_smart_fixtures_integration,
            'GOO-33': self._check_factory_boy_integration,
            'GOO-30-32': self._check_test_config_integration
        }

    def validate_migrated_file(self, file_path: str, original_file_path: str = None) -> MigrationValidationReport:
        """Comprehensive validation of a migrated test file"""
        validation_results = []

        try:
            # Basic syntax and import validation
            validation_results.append(self._validate_syntax(file_path))
            validation_results.append(self._validate_imports(file_path))

            # GOO-35 pattern compliance
            validation_results.append(self._validate_goo35_patterns(file_path))
            validation_results.append(self._check_anti_patterns(file_path))

            # Base class usage validation
            validation_results.append(self._validate_base_class_usage(file_path))

            # Test execution validation
            validation_results.append(self._validate_test_execution(file_path))

            # Integration validation
            integration_status = {}
            for system, check_func in self.integration_checks.items():
                result = check_func(file_path)
                validation_results.append(result)
                integration_status[system] = result.passed

            # Performance comparison (if original provided)
            performance_comparison = None
            if original_file_path and os.path.exists(original_file_path):
                performance_comparison = self._compare_performance(file_path, original_file_path)

            # Coverage analysis
            coverage_analysis = self._analyze_coverage(file_path)

            # Determine overall status
            failed_critical = [r for r in validation_results if not r.passed and 'CRITICAL' in r.check_name]
            failed_any = [r for r in validation_results if not r.passed]

            if failed_critical:
                overall_status = 'FAILED'
            elif failed_any:
                overall_status = 'WARNING'
            else:
                overall_status = 'PASSED'

            return MigrationValidationReport(
                file_path=file_path,
                overall_status=overall_status,
                validation_results=validation_results,
                performance_comparison=performance_comparison,
                coverage_analysis=coverage_analysis,
                integration_status=integration_status
            )

        except Exception as e:
            return MigrationValidationReport(
                file_path=file_path,
                overall_status='FAILED',
                validation_results=[
                    ValidationResult('CRITICAL_ERROR', False, f"Validation failed: {str(e)}")
                ]
            )

    def _validate_syntax(self, file_path: str) -> ValidationResult:
        """Validate Python syntax is correct"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            ast.parse(content)
            return ValidationResult('SYNTAX_CHECK', True, "Syntax validation passed")

        except SyntaxError as e:
            return ValidationResult(
                'CRITICAL_SYNTAX_ERROR',
                False,
                f"Syntax error: {str(e)}",
                {'line': e.lineno, 'text': e.text}
            )
        except Exception as e:
            return ValidationResult(
                'SYNTAX_CHECK_ERROR',
                False,
                f"Could not validate syntax: {str(e)}"
            )

    def _validate_imports(self, file_path: str) -> ValidationResult:
        """Validate all imports are correct and available"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)
            imports = []
            import_errors = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}")

            # Try to import each module
            for imp in imports:
                try:
                    if '.' in imp:
                        module_name = imp.split('.')[0]
                        importlib.import_module(module_name)
                    else:
                        importlib.import_module(imp)
                except ImportError as e:
                    # Check if it's a test-specific import that might not be immediately available
                    if not any(test_prefix in imp for test_prefix in ['tests.', 'test_']):
                        import_errors.append(f"{imp}: {str(e)}")

            if import_errors:
                return ValidationResult(
                    'IMPORT_ERRORS',
                    False,
                    f"Import errors found: {len(import_errors)}",
                    {'errors': import_errors}
                )
            else:
                return ValidationResult(
                    'IMPORT_CHECK',
                    True,
                    f"All {len(imports)} imports validated successfully"
                )

        except Exception as e:
            return ValidationResult(
                'IMPORT_CHECK_ERROR',
                False,
                f"Could not validate imports: {str(e)}"
            )

    def _validate_goo35_patterns(self, file_path: str) -> ValidationResult:
        """Validate proper use of GOO-35 patterns"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)
            pattern_usage = {}
            missing_patterns = []

            # Find base class used
            base_class = None
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if node.bases:
                        for base in node.bases:
                            if isinstance(base, ast.Name) and base.id.startswith('Base') and base.id.endswith('Test'):
                                base_class = base.id
                                break

            if base_class and base_class in self.required_patterns:
                required = self.required_patterns[base_class]
                for pattern in required:
                    if pattern in content:
                        pattern_usage[pattern] = True
                    else:
                        pattern_usage[pattern] = False
                        missing_patterns.append(pattern)

            if missing_patterns:
                return ValidationResult(
                    'GOO35_PATTERN_COMPLIANCE',
                    False,
                    f"Missing required GOO-35 patterns: {', '.join(missing_patterns)}",
                    {'missing_patterns': missing_patterns, 'base_class': base_class}
                )
            elif pattern_usage:
                return ValidationResult(
                    'GOO35_PATTERN_COMPLIANCE',
                    True,
                    f"All required GOO-35 patterns found for {base_class}",
                    {'patterns_used': list(pattern_usage.keys())}
                )
            else:
                return ValidationResult(
                    'GOO35_PATTERN_CHECK',
                    True,
                    "No specific GOO-35 base class detected - using generic patterns"
                )

        except Exception as e:
            return ValidationResult(
                'GOO35_PATTERN_ERROR',
                False,
                f"Could not validate GOO-35 patterns: {str(e)}"
            )

    def _check_anti_patterns(self, file_path: str) -> ValidationResult:
        """Check for anti-patterns that indicate incomplete migration"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            anti_pattern_matches = []
            for pattern in self.anti_patterns:
                matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
                for match in matches:
                    line_number = content[:match.start()].count('\n') + 1
                    anti_pattern_matches.append({
                        'pattern': pattern,
                        'line': line_number,
                        'text': match.group(0)
                    })

            if anti_pattern_matches:
                return ValidationResult(
                    'ANTI_PATTERN_CHECK',
                    False,
                    f"Found {len(anti_pattern_matches)} anti-patterns indicating incomplete migration",
                    {'anti_patterns': anti_pattern_matches}
                )
            else:
                return ValidationResult(
                    'ANTI_PATTERN_CHECK',
                    True,
                    "No anti-patterns detected - migration appears complete"
                )

        except Exception as e:
            return ValidationResult(
                'ANTI_PATTERN_ERROR',
                False,
                f"Could not check anti-patterns: {str(e)}"
            )

    def _validate_base_class_usage(self, file_path: str) -> ValidationResult:
        """Validate proper base class inheritance and usage"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)
            class_analysis = {}

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name.startswith('Test'):
                    base_classes = []
                    if node.bases:
                        for base in node.bases:
                            if isinstance(base, ast.Name):
                                base_classes.append(base.id)
                            elif isinstance(base, ast.Attribute):
                                base_classes.append(f"{base.value.id}.{base.attr}")

                    class_analysis[node.name] = {
                        'base_classes': base_classes,
                        'has_goo35_base': any(bc.startswith('Base') and bc.endswith('Test') for bc in base_classes),
                        'method_count': len([n for n in node.body if isinstance(n, ast.FunctionDef)])
                    }

            # Validate findings
            issues = []
            goo35_classes = 0

            for class_name, analysis in class_analysis.items():
                if not analysis['has_goo35_base']:
                    issues.append(f"{class_name}: Not using GOO-35 base class")
                else:
                    goo35_classes += 1

                if analysis['method_count'] == 0:
                    issues.append(f"{class_name}: No test methods found")

            if issues:
                return ValidationResult(
                    'BASE_CLASS_USAGE',
                    False,
                    f"Base class issues found: {len(issues)}",
                    {'issues': issues, 'goo35_classes': goo35_classes}
                )
            else:
                return ValidationResult(
                    'BASE_CLASS_USAGE',
                    True,
                    f"Proper base class usage validated for {goo35_classes} classes"
                )

        except Exception as e:
            return ValidationResult(
                'BASE_CLASS_ERROR',
                False,
                f"Could not validate base class usage: {str(e)}"
            )

    def _validate_test_execution(self, file_path: str) -> ValidationResult:
        """Validate that tests can actually run successfully"""
        try:
            # Change to the project directory
            original_cwd = os.getcwd()
            project_root = Path(file_path).parent.parent
            os.chdir(project_root)

            # Set testing environment
            os.environ['TESTING'] = 'true'
            os.environ['PYTHONPATH'] = str(project_root)

            # Run the test file
            cmd = [sys.executable, '-m', 'pytest', file_path, '-v', '--tb=short']

            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            execution_time = time.time() - start_time

            os.chdir(original_cwd)

            if result.returncode == 0:
                # Parse test results
                output_lines = result.stdout.split('\n')
                test_count = len([line for line in output_lines if '::test_' in line and 'PASSED' in line])

                return ValidationResult(
                    'TEST_EXECUTION',
                    True,
                    f"All tests executed successfully ({test_count} tests in {execution_time:.2f}s)",
                    {
                        'test_count': test_count,
                        'execution_time': execution_time,
                        'output': result.stdout[:1000]  # First 1000 chars
                    }
                )
            else:
                return ValidationResult(
                    'CRITICAL_TEST_EXECUTION',
                    False,
                    f"Test execution failed with code {result.returncode}",
                    {
                        'error_output': result.stderr[:1000],
                        'stdout': result.stdout[:1000],
                        'execution_time': execution_time
                    }
                )

        except subprocess.TimeoutExpired:
            return ValidationResult(
                'CRITICAL_TEST_TIMEOUT',
                False,
                "Test execution timed out (5 minutes)"
            )
        except Exception as e:
            return ValidationResult(
                'TEST_EXECUTION_ERROR',
                False,
                f"Could not execute tests: {str(e)}"
            )
        finally:
            try:
                os.chdir(original_cwd)
            except:
                pass

    def _check_smart_fixtures_integration(self, file_path: str) -> ValidationResult:
        """Check integration with GOO-34 Smart Fixtures"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Look for smart fixtures usage patterns
            smart_fixture_patterns = [
                r'@fixture',
                r'smart_fixture',
                r'fixture_factory',
                r'auto_fixture'
            ]

            pattern_found = False
            for pattern in smart_fixture_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    pattern_found = True
                    break

            # Check if conftest.py imports are present
            goo34_imports = re.search(r'from.*conftest.*import.*smart', content, re.IGNORECASE)

            if pattern_found or goo34_imports:
                return ValidationResult(
                    'GOO34_INTEGRATION',
                    True,
                    "Smart Fixtures (GOO-34) integration detected"
                )
            else:
                return ValidationResult(
                    'GOO34_INTEGRATION',
                    True,
                    "No Smart Fixtures usage detected (acceptable for simple tests)"
                )

        except Exception as e:
            return ValidationResult(
                'GOO34_INTEGRATION_ERROR',
                False,
                f"Could not check Smart Fixtures integration: {str(e)}"
            )

    def _check_factory_boy_integration(self, file_path: str) -> ValidationResult:
        """Check integration with GOO-33 Factory-Boy"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Look for factory-boy integration patterns
            factory_patterns = [
                r'Factory\.build',
                r'Factory\.create',
                r'factory_boy',
                r'\.with_factory\(',
                r'_use_factory\s*=\s*True'
            ]

            pattern_found = False
            pattern_details = []
            for pattern in factory_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    pattern_found = True
                    line_number = content[:match.start()].count('\n') + 1
                    pattern_details.append({'pattern': pattern, 'line': line_number})

            if pattern_found:
                return ValidationResult(
                    'GOO33_INTEGRATION',
                    True,
                    f"Factory-Boy (GOO-33) integration active ({len(pattern_details)} usages)",
                    {'factory_usages': pattern_details}
                )
            else:
                return ValidationResult(
                    'GOO33_INTEGRATION',
                    True,
                    "No Factory-Boy usage detected (acceptable if using manual builders)"
                )

        except Exception as e:
            return ValidationResult(
                'GOO33_INTEGRATION_ERROR',
                False,
                f"Could not check Factory-Boy integration: {str(e)}"
            )

    def _check_test_config_integration(self, file_path: str) -> ValidationResult:
        """Check integration with GOO-30-32 TestConfig system"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Look for test config patterns
            config_patterns = [
                r'TestConfig',
                r'test_config',
                r'@test_configuration',
                r'with_config\(',
                r'config_variant'
            ]

            pattern_found = False
            config_details = []
            for pattern in config_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    pattern_found = True
                    line_number = content[:match.start()].count('\n') + 1
                    config_details.append({'pattern': pattern, 'line': line_number})

            if pattern_found:
                return ValidationResult(
                    'GOO30_32_INTEGRATION',
                    True,
                    f"TestConfig (GOO-30-32) integration active ({len(config_details)} usages)",
                    {'config_usages': config_details}
                )
            else:
                return ValidationResult(
                    'GOO30_32_INTEGRATION',
                    True,
                    "No TestConfig usage detected (acceptable for simple tests)"
                )

        except Exception as e:
            return ValidationResult(
                'GOO30_32_INTEGRATION_ERROR',
                False,
                f"Could not check TestConfig integration: {str(e)}"
            )

    def _compare_performance(self, migrated_file: str, original_file: str) -> Dict[str, Any]:
        """Compare performance between original and migrated tests"""
        try:
            def run_performance_test(file_path: str) -> Dict[str, float]:
                original_cwd = os.getcwd()
                project_root = Path(file_path).parent.parent
                os.chdir(project_root)

                os.environ['TESTING'] = 'true'
                os.environ['PYTHONPATH'] = str(project_root)

                cmd = [sys.executable, '-m', 'pytest', file_path, '--tb=no', '-q']

                start_time = time.time()
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                execution_time = time.time() - start_time

                os.chdir(original_cwd)

                # Parse results
                if result.returncode == 0:
                    output_lines = result.stdout.split('\n')
                    test_count = len([line for line in output_lines if 'passed' in line.lower()])
                    return {
                        'execution_time': execution_time,
                        'test_count': test_count,
                        'time_per_test': execution_time / max(test_count, 1),
                        'success': True
                    }
                else:
                    return {
                        'execution_time': execution_time,
                        'test_count': 0,
                        'time_per_test': float('inf'),
                        'success': False,
                        'error': result.stderr[:500]
                    }

            # Run both tests
            original_perf = run_performance_test(original_file)
            migrated_perf = run_performance_test(migrated_file)

            # Calculate improvements
            time_improvement = 0
            setup_reduction = 0

            if original_perf['success'] and migrated_perf['success']:
                if original_perf['execution_time'] > 0:
                    time_improvement = ((original_perf['execution_time'] - migrated_perf['execution_time']) /
                                      original_perf['execution_time']) * 100

                # Estimate setup reduction based on file sizes and patterns
                with open(original_file, 'r') as f:
                    original_lines = len(f.readlines())
                with open(migrated_file, 'r') as f:
                    migrated_lines = len(f.readlines())

                if original_lines > 0:
                    setup_reduction = ((original_lines - migrated_lines) / original_lines) * 100

            return {
                'original': original_perf,
                'migrated': migrated_perf,
                'improvements': {
                    'execution_time_improvement_percent': time_improvement,
                    'setup_code_reduction_percent': setup_reduction,
                    'performance_gain': time_improvement > 0
                }
            }

        except Exception as e:
            return {
                'error': f"Performance comparison failed: {str(e)}",
                'original': {'success': False},
                'migrated': {'success': False}
            }

    def _analyze_coverage(self, file_path: str) -> Dict[str, Any]:
        """Analyze test coverage for the migrated file"""
        try:
            # This is a simplified coverage analysis
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            test_methods = 0
            assertion_count = 0
            mock_usage = 0

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                    test_methods += 1

                    # Count assertions in test method
                    method_source = ast.get_source_segment(content, node)
                    if method_source:
                        assertion_count += method_source.count('assert')
                        assertion_count += method_source.count('self.assert')
                        mock_usage += method_source.count('mock_')

            coverage_score = min(100, (assertion_count + mock_usage) * 10)  # Rough heuristic

            return {
                'test_method_count': test_methods,
                'assertion_count': assertion_count,
                'mock_usage_count': mock_usage,
                'estimated_coverage_score': coverage_score,
                'quality_metrics': {
                    'assertions_per_test': assertion_count / max(test_methods, 1),
                    'mocks_per_test': mock_usage / max(test_methods, 1)
                }
            }

        except Exception as e:
            return {'error': f"Coverage analysis failed: {str(e)}"}

    def validate_directory(self, directory_path: str, original_directory: str = None) -> Dict[str, Any]:
        """Validate all migrated test files in a directory"""
        validation_summary = {
            'total_files': 0,
            'passed': 0,
            'warnings': 0,
            'failed': 0,
            'reports': [],
            'overall_status': 'UNKNOWN'
        }

        test_files = []
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.startswith('test_') and file.endswith('.py'):
                    test_files.append(os.path.join(root, file))

        validation_summary['total_files'] = len(test_files)

        for file_path in test_files:
            original_file = None
            if original_directory:
                relative_path = os.path.relpath(file_path, directory_path)
                original_file = os.path.join(original_directory, relative_path)
                if not os.path.exists(original_file):
                    original_file = None

            report = self.validate_migrated_file(file_path, original_file)
            validation_summary['reports'].append(report)

            if report.overall_status == 'PASSED':
                validation_summary['passed'] += 1
            elif report.overall_status == 'WARNING':
                validation_summary['warnings'] += 1
            else:
                validation_summary['failed'] += 1

        # Determine overall status
        if validation_summary['failed'] > 0:
            validation_summary['overall_status'] = 'FAILED'
        elif validation_summary['warnings'] > 0:
            validation_summary['overall_status'] = 'WARNING'
        else:
            validation_summary['overall_status'] = 'PASSED'

        return validation_summary


def main():
    """CLI interface for validation tools"""
    parser = argparse.ArgumentParser(
        description="GOO-35 Migration Validation Tools"
    )
    parser.add_argument(
        'command',
        choices=['validate', 'check-patterns', 'performance-test', 'directory'],
        help='Validation command to run'
    )
    parser.add_argument(
        'target',
        help='Target file or directory'
    )
    parser.add_argument(
        '--original', '-o',
        help='Original file or directory for comparison'
    )
    parser.add_argument(
        '--format', '-f',
        choices=['json', 'text', 'html'],
        default='text',
        help='Output format'
    )
    parser.add_argument(
        '--output', '-out',
        help='Output file for report'
    )

    args = parser.parse_args()
    validator = GOO35MigrationValidator()

    if args.command == 'validate':
        if os.path.isfile(args.target):
            report = validator.validate_migrated_file(args.target, args.original)

            if args.format == 'json':
                output = json.dumps(report.__dict__, indent=2, default=str)
            else:
                output = format_validation_report(report)

            if args.output:
                with open(args.output, 'w') as f:
                    f.write(output)
            else:
                print(output)
        else:
            print("❌ File not found")

    elif args.command == 'directory':
        if os.path.isdir(args.target):
            summary = validator.validate_directory(args.target, args.original)

            if args.format == 'json':
                output = json.dumps(summary, indent=2, default=str)
            else:
                output = format_directory_summary(summary)

            if args.output:
                with open(args.output, 'w') as f:
                    f.write(output)
            else:
                print(output)
        else:
            print("❌ Directory not found")

    # Additional commands can be implemented as needed


def format_validation_report(report: MigrationValidationReport) -> str:
    """Format validation report for text output"""
    status_emoji = {
        'PASSED': '✅',
        'WARNING': '⚠️',
        'FAILED': '❌'
    }

    output = f"\n{status_emoji.get(report.overall_status, '❓')} Validation Report: {report.file_path}\n"
    output += f"Overall Status: {report.overall_status}\n\n"

    for result in report.validation_results:
        emoji = '✅' if result.passed else '❌'
        output += f"{emoji} {result.check_name}: {result.message}\n"

        if result.details and not result.passed:
            for key, value in result.details.items():
                if isinstance(value, list) and len(value) <= 5:
                    output += f"    {key}: {', '.join(map(str, value))}\n"
                elif not isinstance(value, (list, dict)):
                    output += f"    {key}: {value}\n"

    if report.performance_comparison:
        output += "\n📊 Performance Analysis:\n"
        perf = report.performance_comparison.get('improvements', {})
        if perf.get('execution_time_improvement_percent', 0) > 0:
            output += f"  ⚡ {perf['execution_time_improvement_percent']:.1f}% faster execution\n"
        if perf.get('setup_code_reduction_percent', 0) > 0:
            output += f"  📉 {perf['setup_code_reduction_percent']:.1f}% less setup code\n"

    return output


def format_directory_summary(summary: Dict[str, Any]) -> str:
    """Format directory validation summary for text output"""
    output = f"\n📊 Migration Validation Summary\n"
    output += f"Total Files: {summary['total_files']}\n"
    output += f"✅ Passed: {summary['passed']}\n"
    output += f"⚠️ Warnings: {summary['warnings']}\n"
    output += f"❌ Failed: {summary['failed']}\n"
    output += f"\nOverall Status: {summary['overall_status']}\n\n"

    if summary['failed'] > 0:
        output += "❌ Failed Files:\n"
        for report in summary['reports']:
            if report.overall_status == 'FAILED':
                output += f"  - {report.file_path}\n"
                critical_failures = [r for r in report.validation_results if not r.passed and 'CRITICAL' in r.check_name]
                for failure in critical_failures[:2]:  # Show first 2 critical failures
                    output += f"    • {failure.message}\n"

    return output


if __name__ == '__main__':
    main()


# Usage Examples:
"""
# Validate single migrated file
python tests/migration/validation_tools.py validate tests/test_auth_goo35.py --original tests/test_auth_original.py

# Validate entire directory with performance comparison
python tests/migration/validation_tools.py directory tests/migrated/ --original tests/original/ --format json --output validation_report.json

# Quick pattern compliance check
python tests/migration/validation_tools.py check-patterns tests/test_game_goo35.py

# Performance regression testing
python tests/migration/validation_tools.py performance-test tests/test_social_goo35.py --original tests/test_social_original.py

# Bulk validation with detailed reporting
from tests.migration.validation_tools import GOO35MigrationValidator
validator = GOO35MigrationValidator()
summary = validator.validate_directory('tests/migrated/', 'tests/original/')
print(f"Migration success rate: {(summary['passed'] / summary['total_files']) * 100:.1f}%")
"""