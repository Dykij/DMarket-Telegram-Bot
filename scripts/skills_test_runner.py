#!/usr/bin/env python3
"""
Skills Testing Framework

Discovers and runs tests for skills in .github/skills/.
Part of Phase 3 Week 3-4 implementation.
"""

import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple
import json


class SkillTestRunner:
    """Test runner for skills."""

    def __init__(self, skills_dir: Path = Path(".github/skills")):
        self.skills_dir = skills_dir
        self.results: Dict[str, Dict] = {}

    def discover_skills(self) -> List[Path]:
        """Discover all skills with test directories."""
        skills_with_tests = []

        if not self.skills_dir.exists():
            return skills_with_tests

        for skill_path in self.skills_dir.rglob("SKILL.md"):
            skill_dir = skill_path.parent
            tests_dir = skill_dir / "tests"

            if tests_dir.exists() and tests_dir.is_dir():
                test_files = list(tests_dir.glob("test_*.py"))
                if test_files:
                    skills_with_tests.append(skill_dir)

        return skills_with_tests

    def run_tests(self, skill_dir: Path) -> Dict:
        """Run tests for a single skill."""
        skill_name = skill_dir.name
        tests_dir = skill_dir / "tests"

        print(f"\n🧪 Testing: {skill_name}")
        print(f"   Location: {tests_dir}")

        try:
            # Run pytest on the tests directory
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(tests_dir),
                    "-v",
                    "--tb=short",
                    f"--junitxml={tests_dir}/test-results.xml",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Parse output
            passed = result.stdout.count(" PASSED")
            failed = result.stdout.count(" FAILED")
            skipped = result.stdout.count(" SKIPPED")

            test_result = {
                "skill": skill_name,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "exit_code": result.returncode,
                "output": result.stdout,
                "errors": result.stderr,
            }

            # Print summary
            status = "✅" if result.returncode == 0 else "❌"
            print(f"   {status} {passed} passed, {failed} failed, {skipped} skipped")

            return test_result

        except subprocess.TimeoutExpired:
            print(f"   ⏱️ Timeout (>60s)")
            return {
                "skill": skill_name,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "exit_code": -1,
                "output": "",
                "errors": "Test execution timeout",
            }
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {
                "skill": skill_name,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "exit_code": -1,
                "output": "",
                "errors": str(e),
            }

    def run_all_tests(self) -> Tuple[int, int, int]:
        """Run tests for all skills. Returns (passed, failed, skipped)."""
        skills = self.discover_skills()

        if not skills:
            print("ℹ️ No skills with tests found")
            return 0, 0, 0

        print(f"🔍 Found {len(skills)} skill(s) with tests\n")
        print("=" * 60)

        total_passed = 0
        total_failed = 0
        total_skipped = 0

        for skill_dir in skills:
            result = self.run_tests(skill_dir)
            self.results[result["skill"]] = result

            total_passed += result["passed"]
            total_failed += result["failed"]
            total_skipped += result["skipped"]

        print("\n" + "=" * 60)
        print("\n📊 Overall Results:")
        print(f"   ✅ {total_passed} passed")
        print(f"   ❌ {total_failed} failed")
        print(f"   ⏭️ {total_skipped} skipped")

        return total_passed, total_failed, total_skipped

    def generate_report(self, output_file: Path = Path("test-report.json")):
        """Generate JSON test report."""
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Report saved to: {output_file}")


def main():
    """Main CLI for running skill tests."""
    import argparse

    parser = argparse.ArgumentParser(description="Run tests for skills")
    parser.add_argument(
        "--skill", help="Specific skill to test (default: all)", default=None
    )
    parser.add_argument(
        "--report",
        help="Generate JSON report",
        action="store_true",
    )

    args = parser.parse_args()

    runner = SkillTestRunner()

    if args.skill:
        # Test specific skill
        skill_dir = runner.skills_dir / args.skill
        if not skill_dir.exists():
            print(f"❌ Skill '{args.skill}' not found")
            sys.exit(1)

        tests_dir = skill_dir / "tests"
        if not tests_dir.exists():
            print(f"❌ No tests directory for skill '{args.skill}'")
            sys.exit(1)

        result = runner.run_tests(skill_dir)
        sys.exit(0 if result["exit_code"] == 0 else 1)
    else:
        # Test all skills
        passed, failed, skipped = runner.run_all_tests()

        if args.report:
            runner.generate_report()

        sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
