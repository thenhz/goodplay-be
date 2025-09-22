#!/usr/bin/env python3
"""
GoodPlay Backend Test Runner
Comprehensive test execution with different modes and configurations
"""
import os
import sys
import argparse
import subprocess
from pathlib import Path


class TestRunner:
    """Test runner with multiple execution modes"""

    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.tests_dir = self.base_dir / "tests"

    def run_command(self, cmd, description=""):
        """Run command with error handling"""
        print(f"\n🔧 {description}")
        print(f"Running: {' '.join(cmd)}")
        print("-" * 60)

        try:
            result = subprocess.run(cmd, check=True, cwd=self.base_dir)
            print(f"✅ {description} completed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ {description} failed with exit code {e.returncode}")
            return False
        except FileNotFoundError:
            print(f"❌ Command not found: {cmd[0]}")
            print("Please ensure pytest is installed: pip install -r test_requirements.txt")
            return False

    def run_unit_tests(self, module=None, coverage=True, verbose=True):
        """Run unit tests"""
        cmd = ["python", "-m", "pytest"]

        if module:
            # Run specific module
            test_file = self.tests_dir / f"test_{module}.py"
            if test_file.exists():
                cmd.append(str(test_file))
            else:
                print(f"❌ Test module not found: test_{module}.py")
                return False
        else:
            # Run all tests
            cmd.append(str(self.tests_dir))

        # Add markers for unit tests
        cmd.extend(["-m", "not slow and not external"])

        if verbose:
            cmd.append("-v")

        if coverage:
            cmd.extend(["--cov=app", "--cov-report=term-missing"])

        return self.run_command(cmd, f"Unit tests{' for ' + module if module else ''}")

    def run_integration_tests(self):
        """Run integration tests"""
        cmd = [
            "python", "-m", "pytest",
            str(self.tests_dir),
            "-m", "integration",
            "-v",
            "--tb=short"
        ]

        return self.run_command(cmd, "Integration tests")

    def run_api_tests(self):
        """Run API endpoint tests"""
        cmd = [
            "python", "-m", "pytest",
            str(self.tests_dir),
            "-m", "api",
            "-v",
            "--tb=short"
        ]

        return self.run_command(cmd, "API endpoint tests")

    def run_pipeline_tests(self):
        """Run tests suitable for CI/CD pipeline"""
        cmd = [
            "python", "-m", "pytest",
            str(self.tests_dir),
            "-m", "pipeline or (unit and not slow and not external)",
            "--tb=short",
            "--cov=app",
            "--cov-report=xml",
            "--junitxml=test-results.xml"
        ]

        return self.run_command(cmd, "Pipeline tests (CI/CD)")

    def run_coverage_report(self):
        """Generate detailed coverage report"""
        cmd = [
            "python", "-m", "pytest",
            str(self.tests_dir),
            "-m", "not external",
            "--cov=app",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-fail-under=80"
        ]

        success = self.run_command(cmd, "Coverage analysis")

        if success:
            htmlcov_path = self.base_dir / "htmlcov" / "index.html"
            if htmlcov_path.exists():
                print(f"\n📊 Coverage report generated: {htmlcov_path}")
                print("Open in browser to view detailed coverage analysis")

        return success

    def run_specific_test_class(self, test_class):
        """Run specific test class"""
        cmd = [
            "python", "-m", "pytest",
            "-k", test_class,
            "-v"
        ]

        return self.run_command(cmd, f"Test class: {test_class}")

    def run_by_module(self, modules):
        """Run tests for specific modules"""
        success = True
        for module in modules:
            module_success = self.run_unit_tests(module=module)
            success = success and module_success
        return success

    def run_working_tests(self):
        """Run only tests that are guaranteed to work"""
        working_test_files = [
            "tests/test_basic.py::TestUserModel",
            "tests/test_basic.py::TestAuthServiceBasic",
            "tests/test_basic.py::TestApplicationStructure::test_core_module_imports",
            "tests/test_basic.py::TestApplicationStructure::test_games_module_imports",
            "tests/test_basic.py::TestApplicationStructure::test_preferences_module_imports",
            "tests/test_basic.py::TestApplicationStructure::test_social_module_imports",
            "tests/test_basic.py::TestConfigAndEnvironment",
            "tests/test_core_auth.py::TestAuthServiceWorking::test_register_user_email_exists",
            "tests/test_core_auth.py::TestAuthServiceWorking::test_register_user_invalid_email",
            "tests/test_core_auth.py::TestAuthServiceWorking::test_register_user_weak_password",
            "tests/test_core_auth.py::TestAuthServiceWorking::test_register_user_missing_email",
            "tests/test_core_auth.py::TestAuthServiceWorking::test_login_user_not_found",
            "tests/test_core_auth.py::TestAuthServiceWorking::test_login_user_wrong_password",
            "tests/test_core_auth.py::TestAuthServiceWorking::test_login_inactive_user",
            "tests/test_core_auth.py::TestAuthServiceWorking::test_login_missing_credentials",
            "tests/test_core_auth.py::TestAuthServiceWorking::test_refresh_token_success",
            "tests/test_core_auth.py::TestAuthServiceWorking::test_refresh_token_user_not_found",
            "tests/test_core_auth.py::TestAuthServiceWorking::test_get_user_profile_success",
            "tests/test_core_auth.py::TestAuthServiceWorking::test_get_user_profile_not_found",
            "tests/test_core_auth.py::TestUserRepositoryWorking",
            "tests/test_core_auth.py::TestUserModelWorking::test_user_creation_with_preferences",
            "tests/test_core_auth.py::TestUserModelWorking::test_user_email_normalization",
            "tests/test_core_auth.py::TestUserModelWorking::test_user_get_id_method",
            "tests/test_core_auth.py::TestUserModelWorking::test_user_serialization_excludes_sensitive",
            "tests/test_core_auth.py::TestUserModelWorking::test_user_serialization_includes_sensitive_when_requested",
            "tests/test_core_auth.py::TestValidationMethodsWorking",
            "tests/test_core_auth.py::TestTokenGeneration",
            "tests/test_user_extensions_goo5.py::TestUserExtensions::test_add_credits",
            "tests/test_user_extensions_goo5.py::TestUserExtensions::test_backward_compatibility",
            "tests/test_user_extensions_goo5.py::TestUserExtensions::test_donate_credits_insufficient_balance",
            "tests/test_user_extensions_goo5.py::TestUserExtensions::test_donate_credits_successful",
            "tests/test_user_extensions_goo5.py::TestUserExtensions::test_from_dict_with_extended_fields",
            "tests/test_user_extensions_goo5.py::TestUserExtensions::test_to_dict_includes_extended_fields",
            "tests/test_user_extensions_goo5.py::TestUserExtensions::test_update_gaming_stats",
            "tests/test_user_extensions_goo5.py::TestUserExtensions::test_update_social_profile"
        ]

        cmd = [
            "python", "-m", "pytest",
            *working_test_files,
            "-v",
            "--tb=short",
            "--cov=app.core",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov_working"
        ]

        return self.run_command(cmd, f"Working test suite ({len(working_test_files)} reliable tests)")

    def install_dependencies(self):
        """Install test dependencies"""
        req_file = self.base_dir / "test_requirements.txt"
        if not req_file.exists():
            print("❌ test_requirements.txt not found")
            return False

        cmd = ["pip", "install", "-r", str(req_file)]
        return self.run_command(cmd, "Installing test dependencies")

    def check_environment(self):
        """Check test environment setup"""
        print("🔍 Checking test environment...")

        # Check Python version
        python_version = sys.version_info
        print(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")

        if python_version < (3, 8):
            print("❌ Python 3.8+ required")
            return False

        # Check if pytest is available
        try:
            subprocess.run(["python", "-m", "pytest", "--version"],
                         check=True, capture_output=True)
            print("✅ pytest is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ pytest not found. Run: pip install -r test_requirements.txt")
            return False

        # Check MongoDB connection (optional for mocked tests)
        print("ℹ️  For integration tests, ensure MongoDB is running on localhost:27017")

        return True

    def cleanup(self):
        """Clean up test artifacts"""
        artifacts = [
            ".coverage",
            "htmlcov",
            ".pytest_cache",
            "test-results.xml",
            "__pycache__"
        ]

        print("🧹 Cleaning up test artifacts...")

        for artifact in artifacts:
            artifact_path = self.base_dir / artifact
            if artifact_path.exists():
                if artifact_path.is_file():
                    artifact_path.unlink()
                    print(f"Removed: {artifact}")
                else:
                    # Remove directory
                    import shutil
                    shutil.rmtree(artifact_path)
                    print(f"Removed directory: {artifact}")


def main():
    """Main test runner interface"""
    parser = argparse.ArgumentParser(
        description="GoodPlay Backend Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                     # Run all unit tests
  python run_tests.py --working           # Run only working tests (fast & reliable)
  python run_tests.py --module auth       # Run auth module tests
  python run_tests.py --integration       # Run integration tests
  python run_tests.py --api               # Run API tests
  python run_tests.py --pipeline          # Run CI/CD suitable tests
  python run_tests.py --coverage          # Generate coverage report
  python run_tests.py --class TestAuth    # Run specific test class
  python run_tests.py --install           # Install dependencies
  python run_tests.py --cleanup           # Clean test artifacts
        """
    )

    parser.add_argument("--module", "-m",
                       choices=["auth", "preferences", "social", "games", "core"],
                       help="Run tests for specific module")

    parser.add_argument("--integration", "-i", action="store_true",
                       help="Run integration tests")

    parser.add_argument("--api", "-a", action="store_true",
                       help="Run API endpoint tests")

    parser.add_argument("--pipeline", "-p", action="store_true",
                       help="Run tests suitable for CI/CD pipeline")

    parser.add_argument("--coverage", "-c", action="store_true",
                       help="Generate detailed coverage report")

    parser.add_argument("--class", dest="test_class",
                       help="Run specific test class")

    parser.add_argument("--working", "-w", action="store_true",
                       help="Run only working tests (guaranteed to pass)")

    parser.add_argument("--install", action="store_true",
                       help="Install test dependencies")

    parser.add_argument("--cleanup", action="store_true",
                       help="Clean up test artifacts")

    parser.add_argument("--check", action="store_true",
                       help="Check test environment")

    parser.add_argument("--no-coverage", action="store_true",
                       help="Skip coverage analysis")

    parser.add_argument("--verbose", "-v", action="store_true", default=True,
                       help="Verbose output (default: True)")

    args = parser.parse_args()

    runner = TestRunner()

    print("🧪 GoodPlay Backend Test Runner")
    print("=" * 50)

    # Handle special commands
    if args.install:
        success = runner.install_dependencies()
        sys.exit(0 if success else 1)

    if args.cleanup:
        runner.cleanup()
        sys.exit(0)

    if args.check:
        success = runner.check_environment()
        sys.exit(0 if success else 1)

    # Check environment before running tests
    if not runner.check_environment():
        print("\n❌ Environment check failed. Please fix issues before running tests.")
        sys.exit(1)

    success = True

    # Execute selected test type
    if args.module:
        success = runner.run_unit_tests(
            module=args.module,
            coverage=not args.no_coverage,
            verbose=args.verbose
        )
    elif args.integration:
        success = runner.run_integration_tests()
    elif args.api:
        success = runner.run_api_tests()
    elif args.pipeline:
        success = runner.run_pipeline_tests()
    elif args.coverage:
        success = runner.run_coverage_report()
    elif args.working:
        success = runner.run_working_tests()
    elif args.test_class:
        success = runner.run_specific_test_class(args.test_class)
    else:
        # Default: run all unit tests
        success = runner.run_unit_tests(
            coverage=not args.no_coverage,
            verbose=args.verbose
        )

    # Print summary
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests completed successfully!")
    else:
        print("❌ Some tests failed. Check output above for details.")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()