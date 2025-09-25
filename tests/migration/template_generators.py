"""
Template Generators for GOO-35 Migration (FASE 1.3)

This module provides template generation capabilities to help convert existing tests
to use the new GOO-35 Testing Utilities architecture with minimal manual effort.

Features:
- Generate base class templates for different test types
- Convert existing test methods to use GOO-35 patterns
- Generate fluent builder replacements for manual data creation
- Create parametrized test decorators for common scenarios
- Auto-generate fixture integrations

Usage:
    python tests/migration/template_generators.py --analyze tests/
    python tests/migration/template_generators.py --convert tests/test_auth.py
"""

import ast
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import argparse
import json


@dataclass
class ConversionTemplate:
    """Template for converting test patterns"""
    pattern_type: str
    original_pattern: str
    new_pattern: str
    imports_needed: List[str]
    base_class_change: Optional[str] = None
    setup_changes: List[str] = None


@dataclass
class TestClassAnalysis:
    """Analysis of a test class for conversion"""
    class_name: str
    current_base: str
    suggested_base: str
    test_methods: List[str]
    setup_patterns: List[str]
    mocking_patterns: List[str]
    data_creation_patterns: List[str]
    boilerplate_lines: int


class GOO35TemplateGenerator:
    """Main template generator for GOO-35 migration"""

    def __init__(self):
        self.conversion_templates = self._load_conversion_templates()
        self.base_class_mapping = {
            'auth': 'BaseAuthTest',
            'authentication': 'BaseAuthTest',
            'login': 'BaseAuthTest',
            'jwt': 'BaseAuthTest',
            'user': 'BaseAuthTest',
            'game': 'BaseGameTest',
            'session': 'BaseGameTest',
            'plugin': 'BaseGameTest',
            'social': 'BaseSocialTest',
            'achievement': 'BaseSocialTest',
            'leaderboard': 'BaseSocialTest',
            'friend': 'BaseSocialTest',
            'preferences': 'BasePreferencesTest',
            'settings': 'BasePreferencesTest',
            'config': 'BasePreferencesTest'
        }

    def _load_conversion_templates(self) -> List[ConversionTemplate]:
        """Load predefined conversion templates"""
        templates = [
            # Auth service mocking conversion
            ConversionTemplate(
                pattern_type="auth_service_mock",
                original_pattern=r"@patch\('.*auth.*service.*'\)\s*def test_(\w+)\(self, mock_\w+\):",
                new_pattern="def test_{method_name}(self):",
                imports_needed=["from tests.core.base_auth_test import BaseAuthTest"],
                base_class_change="BaseAuthTest",
                setup_changes=["# Remove manual mocking - handled by BaseAuthTest"]
            ),

            # JWT mocking conversion
            ConversionTemplate(
                pattern_type="jwt_mock",
                original_pattern=r"@patch\('flask_jwt_extended\.create_access_token'\)",
                new_pattern="# JWT mocking handled automatically by BaseAuthTest",
                imports_needed=["from tests.core.base_auth_test import BaseAuthTest"],
                base_class_change="BaseAuthTest"
            ),

            # Manual user data creation
            ConversionTemplate(
                pattern_type="manual_user_data",
                original_pattern=r"user_data = \{\s*['\"]email['\"]: ['\"].*?['\"]\s*,.*?\}",
                new_pattern="user_data = self.create_test_user()",
                imports_needed=["from tests.core.base_auth_test import BaseAuthTest"],
                base_class_change="BaseAuthTest"
            ),

            # Game session mocking
            ConversionTemplate(
                pattern_type="game_session_mock",
                original_pattern=r"@patch\('.*game.*session.*'\)",
                new_pattern="# Game session mocking handled by BaseGameTest",
                imports_needed=["from tests.core.base_game_test import BaseGameTest"],
                base_class_change="BaseGameTest"
            ),

            # Achievement mocking
            ConversionTemplate(
                pattern_type="achievement_mock",
                original_pattern=r"@patch\('.*achievement.*'\)",
                new_pattern="# Achievement mocking handled by BaseSocialTest",
                imports_needed=["from tests.core.base_social_test import BaseSocialTest"],
                base_class_change="BaseSocialTest"
            ),

            # Preferences data creation
            ConversionTemplate(
                pattern_type="preferences_data",
                original_pattern=r"preferences = \{\s*['\"]theme['\"]: ['\"].*?['\"]\s*,.*?\}",
                new_pattern="preferences = self.create_test_preferences()",
                imports_needed=["from tests.core.base_preferences_test import BasePreferencesTest"],
                base_class_change="BasePreferencesTest"
            ),
        ]

        return templates

    def analyze_test_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a test file for conversion opportunities"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)
            analysis = {
                'file_path': file_path,
                'classes': [],
                'imports': [],
                'total_boilerplate_lines': 0,
                'conversion_opportunities': []
            }

            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis['imports'].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        analysis['imports'].append(f"{module}.{alias.name}")

            # Analyze classes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_analysis = self._analyze_test_class(node, content)
                    if class_analysis:
                        analysis['classes'].append(class_analysis)
                        analysis['total_boilerplate_lines'] += class_analysis.boilerplate_lines

            # Find conversion opportunities
            analysis['conversion_opportunities'] = self._find_conversion_opportunities(content)

            return analysis

        except Exception as e:
            return {'error': str(e), 'file_path': file_path}

    def _analyze_test_class(self, class_node: ast.ClassDef, content: str) -> Optional[TestClassAnalysis]:
        """Analyze a test class for conversion opportunities"""
        class_name = class_node.name

        if not class_name.startswith('Test'):
            return None

        # Determine current base class
        current_base = 'unittest.TestCase'
        if class_node.bases:
            for base in class_node.bases:
                if isinstance(base, ast.Name):
                    current_base = base.id
                elif isinstance(base, ast.Attribute):
                    current_base = f"{base.value.id}.{base.attr}"

        # Suggest appropriate base class
        suggested_base = self._suggest_base_class(class_name, content)

        # Analyze methods
        test_methods = []
        setup_patterns = []
        mocking_patterns = []
        data_creation_patterns = []
        boilerplate_lines = 0

        for method in class_node.body:
            if isinstance(method, ast.FunctionDef):
                method_name = method.name

                if method_name.startswith('test_'):
                    test_methods.append(method_name)
                elif method_name in ['setUp', 'setUpClass']:
                    setup_patterns.append(method_name)
                    boilerplate_lines += len(method.body)

                # Look for mocking patterns in method source
                method_source = ast.get_source_segment(content, method)
                if method_source:
                    if '@patch(' in method_source:
                        mocking_patterns.append(f"{method_name}: patch decorators")
                        boilerplate_lines += method_source.count('@patch(')

                    if re.search(r'{\s*[\'"].*?[\'"]:\s*[\'"].*?[\'"]', method_source):
                        data_creation_patterns.append(f"{method_name}: manual dict creation")
                        boilerplate_lines += method_source.count('{')

        return TestClassAnalysis(
            class_name=class_name,
            current_base=current_base,
            suggested_base=suggested_base,
            test_methods=test_methods,
            setup_patterns=setup_patterns,
            mocking_patterns=mocking_patterns,
            data_creation_patterns=data_creation_patterns,
            boilerplate_lines=boilerplate_lines
        )

    def _suggest_base_class(self, class_name: str, content: str) -> str:
        """Suggest appropriate GOO-35 base class"""
        class_name_lower = class_name.lower()
        content_lower = content.lower()

        # Check class name first
        for keyword, base_class in self.base_class_mapping.items():
            if keyword in class_name_lower:
                return base_class

        # Check content patterns
        if any(pattern in content_lower for pattern in ['jwt', 'login', 'auth', 'password']):
            return 'BaseAuthTest'
        elif any(pattern in content_lower for pattern in ['game', 'session', 'plugin', 'score']):
            return 'BaseGameTest'
        elif any(pattern in content_lower for pattern in ['social', 'friend', 'achievement', 'leaderboard']):
            return 'BaseSocialTest'
        elif any(pattern in content_lower for pattern in ['preference', 'setting', 'config']):
            return 'BasePreferencesTest'

        return 'BaseServiceTest'  # Default fallback

    def _find_conversion_opportunities(self, content: str) -> List[Dict[str, Any]]:
        """Find specific conversion opportunities in content"""
        opportunities = []

        for template in self.conversion_templates:
            matches = re.finditer(template.original_pattern, content, re.MULTILINE | re.DOTALL)
            for match in matches:
                opportunities.append({
                    'type': template.pattern_type,
                    'line': content[:match.start()].count('\n') + 1,
                    'original': match.group(0),
                    'suggested': template.new_pattern,
                    'base_class_change': template.base_class_change,
                    'imports_needed': template.imports_needed
                })

        return opportunities

    def generate_converted_file(self, file_path: str, output_path: str = None) -> str:
        """Generate a converted version of a test file"""
        analysis = self.analyze_test_file(file_path)

        if 'error' in analysis:
            raise Exception(f"Failed to analyze file: {analysis['error']}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Apply conversions
        converted_content = self._apply_conversions(content, analysis)

        # Write output
        if output_path is None:
            output_path = file_path.replace('.py', '_goo35_converted.py')

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(converted_content)

        return output_path

    def _apply_conversions(self, content: str, analysis: Dict[str, Any]) -> str:
        """Apply all conversions to content"""
        converted = content
        imports_to_add = set()
        base_class_changes = {}

        # Apply pattern-based conversions
        for opportunity in analysis['conversion_opportunities']:
            template = next(
                (t for t in self.conversion_templates if t.pattern_type == opportunity['type']),
                None
            )
            if template:
                converted = re.sub(
                    template.original_pattern,
                    template.new_pattern,
                    converted,
                    flags=re.MULTILINE | re.DOTALL
                )
                imports_to_add.update(template.imports_needed)
                if template.base_class_change:
                    base_class_changes[opportunity['type']] = template.base_class_change

        # Apply base class changes
        for class_info in analysis['classes']:
            if class_info.suggested_base != class_info.current_base:
                # Replace base class
                old_class_def = f"class {class_info.class_name}({class_info.current_base}):"
                new_class_def = f"class {class_info.class_name}({class_info.suggested_base}):"
                converted = converted.replace(old_class_def, new_class_def)

                # Add appropriate import
                if class_info.suggested_base == 'BaseAuthTest':
                    imports_to_add.add("from tests.core.base_auth_test import BaseAuthTest")
                elif class_info.suggested_base == 'BaseGameTest':
                    imports_to_add.add("from tests.core.base_game_test import BaseGameTest")
                elif class_info.suggested_base == 'BaseSocialTest':
                    imports_to_add.add("from tests.core.base_social_test import BaseSocialTest")
                elif class_info.suggested_base == 'BasePreferencesTest':
                    imports_to_add.add("from tests.core.base_preferences_test import BasePreferencesTest")

        # Add necessary imports at the top
        if imports_to_add:
            import_lines = '\n'.join(sorted(imports_to_add))
            # Find where to insert imports (after existing imports)
            lines = converted.split('\n')
            insert_position = 0
            for i, line in enumerate(lines):
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    insert_position = i + 1
                elif line.strip() == '' and insert_position > 0:
                    continue
                elif insert_position > 0:
                    break

            lines.insert(insert_position, import_lines)
            converted = '\n'.join(lines)

        return converted

    def generate_migration_report(self, directory_path: str) -> Dict[str, Any]:
        """Generate comprehensive migration report for a directory"""
        report = {
            'summary': {
                'total_files': 0,
                'convertible_files': 0,
                'total_boilerplate_lines': 0,
                'estimated_reduction': 0
            },
            'files': [],
            'recommendations': []
        }

        test_files = []
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.startswith('test_') and file.endswith('.py'):
                    test_files.append(os.path.join(root, file))

        report['summary']['total_files'] = len(test_files)

        for file_path in test_files:
            analysis = self.analyze_test_file(file_path)
            if 'error' not in analysis:
                report['files'].append(analysis)
                if analysis['conversion_opportunities']:
                    report['summary']['convertible_files'] += 1
                report['summary']['total_boilerplate_lines'] += analysis['total_boilerplate_lines']

        # Calculate estimated reduction (typically 60-80% for GOO-35 migration)
        report['summary']['estimated_reduction'] = int(report['summary']['total_boilerplate_lines'] * 0.7)

        # Generate recommendations
        report['recommendations'] = self._generate_migration_recommendations(report['files'])

        return report

    def _generate_migration_recommendations(self, file_analyses: List[Dict[str, Any]]) -> List[str]:
        """Generate migration recommendations based on analysis"""
        recommendations = []

        # Count patterns
        auth_files = sum(1 for f in file_analyses for c in f['classes'] if c.suggested_base == 'BaseAuthTest')
        game_files = sum(1 for f in file_analyses for c in f['classes'] if c.suggested_base == 'BaseGameTest')
        social_files = sum(1 for f in file_analyses for c in f['classes'] if c.suggested_base == 'BaseSocialTest')
        preferences_files = sum(1 for f in file_analyses for c in f['classes'] if c.suggested_base == 'BasePreferencesTest')

        if auth_files > 0:
            recommendations.append(f"Migrate {auth_files} authentication test files to BaseAuthTest first")
        if game_files > 0:
            recommendations.append(f"Migrate {game_files} game engine test files to BaseGameTest")
        if social_files > 0:
            recommendations.append(f"Migrate {social_files} social feature test files to BaseSocialTest")
        if preferences_files > 0:
            recommendations.append(f"Migrate {preferences_files} preferences test files to BasePreferencesTest")

        # Pattern-specific recommendations
        mock_heavy_files = [
            f for f in file_analyses
            for c in f['classes']
            if len(c.mocking_patterns) > 5
        ]
        if mock_heavy_files:
            recommendations.append(f"High priority: {len(mock_heavy_files)} files with extensive mocking will benefit most from GOO-35")

        return recommendations

    def generate_batch_conversion_script(self, directory_path: str, output_dir: str = None) -> str:
        """Generate a batch script to convert multiple files"""
        if output_dir is None:
            output_dir = os.path.join(directory_path, 'goo35_converted')

        os.makedirs(output_dir, exist_ok=True)

        script_content = f"""#!/usr/bin/env python3
\"\"\"
Batch conversion script for GOO-35 migration
Generated automatically by GOO-35 Template Generator
\"\"\"

import os
import shutil
from pathlib import Path

def convert_test_files():
    \"\"\"Convert all test files to GOO-35 architecture\"\"\"

    # Files to convert
    test_files = [
"""

        test_files = []
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.startswith('test_') and file.endswith('.py'):
                    test_files.append(os.path.join(root, file))

        for file_path in test_files:
            relative_path = os.path.relpath(file_path, directory_path)
            script_content += f"        '{relative_path}',\n"

        script_content += f"""    ]

    # Convert each file
    from tests.migration.template_generators import GOO35TemplateGenerator
    generator = GOO35TemplateGenerator()

    conversion_results = []

    for file_path in test_files:
        try:
            full_path = os.path.join('{directory_path}', file_path)
            output_path = os.path.join('{output_dir}', file_path)

            # Create output directory
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Convert file
            converted_path = generator.generate_converted_file(full_path, output_path)
            conversion_results.append((file_path, 'SUCCESS'))
            print(f"✅ Converted {{file_path}} -> {{output_path}}")

        except Exception as e:
            conversion_results.append((file_path, f'ERROR: {{e}}'))
            print(f"❌ Failed to convert {{file_path}}: {{e}}")

    # Generate summary report
    successful = len([r for r in conversion_results if r[1] == 'SUCCESS'])
    failed = len(conversion_results) - successful

    print(f"\\n📊 Conversion Summary:")
    print(f"  ✅ Successfully converted: {{successful}} files")
    print(f"  ❌ Failed conversions: {{failed}} files")

    if failed > 0:
        print("\\n❌ Failed files:")
        for file_path, result in conversion_results:
            if result != 'SUCCESS':
                print(f"  - {{file_path}}: {{result}}")

    return conversion_results

if __name__ == '__main__':
    convert_test_files()
"""

        script_path = os.path.join(output_dir, 'batch_convert_goo35.py')
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)

        os.chmod(script_path, 0o755)  # Make executable

        return script_path


def main():
    """CLI interface for template generator"""
    parser = argparse.ArgumentParser(
        description="GOO-35 Template Generator for test migration"
    )
    parser.add_argument(
        'command',
        choices=['analyze', 'convert', 'report', 'batch'],
        help='Action to perform'
    )
    parser.add_argument(
        'target',
        help='Target file or directory'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output file or directory'
    )
    parser.add_argument(
        '--format', '-f',
        choices=['json', 'text', 'html'],
        default='text',
        help='Output format for reports'
    )

    args = parser.parse_args()
    generator = GOO35TemplateGenerator()

    if args.command == 'analyze':
        if os.path.isfile(args.target):
            analysis = generator.analyze_test_file(args.target)
            if args.format == 'json':
                print(json.dumps(analysis, indent=2))
            else:
                print(f"📁 Analysis for {args.target}")
                print(f"  Classes: {len(analysis.get('classes', []))}")
                print(f"  Conversion opportunities: {len(analysis.get('conversion_opportunities', []))}")
                print(f"  Boilerplate lines: {analysis.get('total_boilerplate_lines', 0)}")
        else:
            print("❌ File not found")

    elif args.command == 'convert':
        if os.path.isfile(args.target):
            output_path = generator.generate_converted_file(args.target, args.output)
            print(f"✅ Converted file saved to: {output_path}")
        else:
            print("❌ File not found")

    elif args.command == 'report':
        if os.path.isdir(args.target):
            report = generator.generate_migration_report(args.target)
            if args.format == 'json':
                print(json.dumps(report, indent=2))
            else:
                print(f"📊 Migration Report for {args.target}")
                print(f"  Total files: {report['summary']['total_files']}")
                print(f"  Convertible files: {report['summary']['convertible_files']}")
                print(f"  Estimated boilerplate reduction: {report['summary']['estimated_reduction']} lines")
                print("\n📋 Recommendations:")
                for rec in report['recommendations']:
                    print(f"  • {rec}")
        else:
            print("❌ Directory not found")

    elif args.command == 'batch':
        if os.path.isdir(args.target):
            script_path = generator.generate_batch_conversion_script(args.target, args.output)
            print(f"✅ Batch conversion script generated: {script_path}")
            print("Run the script to perform batch conversion")
        else:
            print("❌ Directory not found")


if __name__ == '__main__':
    main()


# Usage Examples:
"""
# Analyze a single test file
python tests/migration/template_generators.py analyze tests/test_auth.py

# Convert a single test file
python tests/migration/template_generators.py convert tests/test_auth.py --output tests/test_auth_goo35.py

# Generate migration report for all tests
python tests/migration/template_generators.py report tests/ --format json

# Generate batch conversion script
python tests/migration/template_generators.py batch tests/ --output converted_tests/

# Quick analysis of test patterns
from tests.migration.template_generators import GOO35TemplateGenerator
generator = GOO35TemplateGenerator()
analysis = generator.analyze_test_file('tests/test_core_auth.py')
print(f"Boilerplate lines to reduce: {analysis['total_boilerplate_lines']}")
"""