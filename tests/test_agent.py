"""
Agentic Test Manager for Knowledge Base GraphRAG System (2026)
Self-evolving test orchestration that tracks, analyzes, and improves tests over time.
"""

import json
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

console = Console()


@dataclass
class TestResult:
    """Represents a single test result"""

    test_id: str
    test_file: str
    test_name: str
    status: str
    duration: float
    timestamp: str
    error_message: str | None = None
    coverage: float | None = None


@dataclass
class TestSuite:
    """Represents a collection of tests for a module"""

    module_name: str
    test_file: str
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    duration: float = 0.0
    last_run: str | None = None


@dataclass
class TestEvolution:
    """Tracks how tests have evolved over time"""

    test_id: str
    history: list[TestResult]
    trend: str
    suggestion: str | None = None


class AgenticTestManager:
    """Intelligent test orchestration system."""

    def __init__(self, history_file: str = "tests/test_history.json"):
        self.history_file = Path(history_file)
        self.suites: dict[str, TestSuite] = {}
        self.evolution: dict[str, TestEvolution] = {}
        self._load_history()

    def _load_history(self):
        """Load test history from persistent storage"""
        if self.history_file.exists():
            try:
                with open(self.history_file) as f:
                    data = json.load(f)
                    self.suites = {
                        k: TestSuite(**v) for k, v in data.get("suites", {}).items()
                    }
                    self.evolution = {
                        k: TestEvolution(**v)
                        for k, v in data.get("evolution", {}).items()
                    }
            except Exception as e:
                console.print(f"[yellow]Failed to load test history: {e}[/yellow]")

    def _save_history(self):
        """Save test history to persistent storage"""
        try:
            data = {
                "suites": {k: asdict(v) for k, v in self.suites.items()},
                "evolution": {k: asdict(v) for k, v in self.evolution.items()},
            }
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            console.print(f"[red]Failed to save test history: {e}[/red]")

    def run_tests(self, pattern: str = "tests/test_*.py") -> dict[str, TestSuite]:
        """Run all tests and collect results using pytest"""
        console.print(
            Panel.fit(
                "[bold blue]🚀 Running Agentic Test Suite[/bold blue]", padding=(1, 1)
            )
        )

        xml_output = Path("test_results.xml")
        cmd = [
            "uv",
            "run",
            "pytest",
            pattern,
            "--junitxml=test_results.xml",
            "--tb=short",
            "-v",
        ]

        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            suites = self._parse_junit_xml(xml_output) if xml_output.exists() else {}

            for suite_name, suite in suites.items():
                suite.last_run = datetime.now().isoformat()
                self.suites[suite_name] = suite

            if xml_output.exists():
                xml_output.unlink()

            return suites

        except subprocess.TimeoutExpired:
            console.print("[red]⏱ Tests timed out after 5 minutes[/red]")
            return {}
        except Exception as e:
            console.print(f"[red]❌ Test execution failed: {e}[/red]")
            return {}

    def _parse_junit_xml(self, xml_file: Path) -> dict[str, TestSuite]:
        """Parse pytest JUnit XML output"""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            module_tests: dict[str, dict] = {}

            for testsuite in root.findall("testsuite"):
                for testcase in testsuite.findall("testcase"):
                    classname = testcase.get("classname", "")
                    time = float(testcase.get("time", "0"))

                    module_name = "unknown"
                    if "test_" in classname:
                        parts = classname.split(".")
                        for part in reversed(parts):
                            if part.startswith("test_"):
                                module_name = part.replace("test_", "")
                                break

                    if module_name not in module_tests:
                        module_tests[module_name] = {
                            "passed": 0,
                            "failed": 0,
                            "skipped": 0,
                            "total": 0,
                            "time": 0.0,
                        }

                    module_tests[module_name]["total"] += 1
                    module_tests[module_name]["time"] += time

                    skipped = testcase.find("skipped")
                    failure = testcase.find("failure")
                    error = testcase.find("error")

                    if skipped is not None:
                        module_tests[module_name]["skipped"] += 1
                    elif failure is not None or error is not None:
                        module_tests[module_name]["failed"] += 1
                    else:
                        module_tests[module_name]["passed"] += 1

            suites: dict[str, TestSuite] = {}
            for module, stats in module_tests.items():
                suite = TestSuite(
                    module_name=module,
                    test_file="pytest",
                    total_tests=stats["total"],
                    passed=stats["passed"],
                    failed=stats["failed"],
                    skipped=stats["skipped"],
                    duration=round(stats["time"], 3),
                    last_run=datetime.now().isoformat(),
                )
                suites[module] = suite

            return suites

        except Exception as e:
            console.print(f"[yellow]Failed to parse JUnit XML: {e}[/yellow]")
            return {}

    def analyze_results(self, suites: dict[str, TestSuite]) -> list[str]:
        """Analyze test results and provide actionable insights"""
        suggestions = []

        total_passed = sum(suite.passed for suite in suites.values())
        total_tests = sum(suite.total_tests for suite in suites.values())
        pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

        if pass_rate < 80:
            suggestions.append(
                "⚠️  Low pass rate (<80%). Review failing tests and fix critical issues."
            )
        elif pass_rate == 100:
            suggestions.append("✅ Perfect pass rate! Consider adding edge case tests.")

        for suite in suites.values():
            if suite.total_tests < 5:
                suggestions.append(
                    f"📊 Low test coverage for {suite.module_name}. Add more comprehensive tests."
                )
            if suite.duration > 30:
                suggestions.append(
                    f"⏱ Slow test suite: {suite.module_name} took {suite.duration:.1f}s."
                )

        suggestions.extend(self._generate_test_suggestions())
        return suggestions

    def _generate_test_suggestions(self) -> list[str]:
        """Analyze codebase and suggest new tests to write"""
        from pathlib import Path

        suggestions = []
        tested_modules = set(self.suites.keys())

        test_files = list(Path("tests").glob("test_*.py"))
        existing_modules = {
            f.stem.replace("test_", "")
            for f in test_files
            if f.stem.startswith("test_")
        }

        all_modules = [
            "pipeline",
            "resolver",
            "ingestor",
            "community",
            "summarizer",
            "api",
            "websocket",
        ]

        for module in all_modules:
            if module not in tested_modules and module not in existing_modules:
                suggestions.append(
                    f"📝 Missing test suite for module: {module}. Create test_{module}.py"
                )

        return suggestions

    def suggest_new_tests(self, module: str) -> list[str]:
        """Suggest tests for a specific module"""
        suggestions = []
        module_file = f"test_{module}.py"
        test_file = Path(f"tests/{module_file}")

        if not test_file.exists():
            suggestions.append(f"📝 Create {module_file} for the {module} module")
            suggestions.append("   - Test core functionality")
            suggestions.append("   - Test edge cases and error handling")
            suggestions.append("   - Test integration with dependencies")

        if module == "api":
            suggestions.extend(
                [
                    "   - Test all API endpoints with various request parameters",
                    "   - Test authentication and authorization",
                    "   - Test rate limiting and error responses",
                ]
            )
        elif module == "community":
            suggestions.extend(
                [
                    "   - Test with different graph sizes",
                    "   - Test hierarchical community detection",
                    "   - Test database integration",
                ]
            )
        elif module == "summarizer":
            suggestions.extend(
                [
                    "   - Test recursive summarization logic",
                    "   - Test with different community structures",
                    "   - Test LLM integration",
                ]
            )
        elif module == "websocket":
            suggestions.extend(
                [
                    "   - Test real-time update mechanisms",
                    "   - Test connection handling",
                    "   - Test message formatting",
                ]
            )

        return suggestions

    def visualize_results(self, suites: dict[str, TestSuite], suggestions: list[str]):
        """Display test results in a beautiful, organized format"""
        console.print("\n")

        summary_table = Table(title="📋 Test Execution Summary")
        summary_table.add_column("Module", style="cyan")
        summary_table.add_column("Total", style="magenta")
        summary_table.add_column("Passed", style="green")
        summary_table.add_column("Failed", style="red")
        summary_table.add_column("Duration", style="blue")

        for suite_name, suite in sorted(suites.items()):
            summary_table.add_row(
                suite_name.replace("test_", ""),
                str(suite.total_tests),
                str(suite.passed),
                str(suite.failed),
                f"{suite.duration:.2f}s",
            )

        console.print(summary_table)

        if suggestions:
            suggestions_tree = Tree("💡 AI Suggestions")
            for suggestion in suggestions:
                suggestions_tree.add(suggestion)
            console.print(
                Panel.fit(
                    suggestions_tree,
                    title="[bold yellow]Intelligent Insights[/bold yellow]",
                )
            )

        self._display_trends()
        console.print("\n")

    def _display_trends(self):
        """Display historical trends for tests"""
        if not self.evolution:
            return

        trends_table = Table(title="📈 Test Trends (History)")
        trends_table.add_column("Test ID", style="cyan")
        trends_table.add_column("Runs", style="magenta")
        trends_table.add_column("Trend", style="white")
        trends_table.add_column("Suggestion", style="yellow")

        for test_id, evolution in sorted(
            self.evolution.items(), key=lambda x: len(x[1].history), reverse=True
        )[:10]:
            trend_symbol = {
                "IMPROVING": "📈",
                "REGRESSING": "📉",
                "STABLE": "➡️",
                "UNKNOWN": "❓",
            }.get(evolution.trend, "❓")
            trends_table.add_row(
                test_id,
                str(len(evolution.history)),
                f"{trend_symbol} {evolution.trend}",
                evolution.suggestion or "-",
            )

        console.print(trends_table)

    def generate_test_report(self, suites: dict[str, TestSuite]) -> str:
        """Generate comprehensive test report in Markdown format"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report = f"""# Test Execution Report
**Generated**: {timestamp}
**Test Manager**: Agentic AI Test System (2026)

## Summary
- **Total Test Suites**: {len(suites)}
- **Total Tests**: {sum(s.total_tests for s in suites.values())}
- **Passed**: {sum(s.passed for s in suites.values())}
- **Failed**: {sum(s.failed for s in suites.values())}
- **Duration**: {sum(s.duration for s in suites.values()):.2f}s

## Test Suite Details
"""
        for suite_name, suite in sorted(suites.items()):
            report += f"""
### {suite_name.replace("test_", "").title()}
- **Status**: {"✅ PASS" if suite.failed == 0 else "❌ FAIL"}
- **Total**: {suite.total_tests}
- **Passed**: {suite.passed}
- **Failed**: {suite.failed}
- **Duration**: {suite.duration:.2f}s
"""
        report += "\n---\n*Generated by Agentic Test Manager*\n"
        return report

    def save_report(self, report: str, filename: str = "test_report.md"):
        """Save test report to file"""
        report_path = Path(filename)
        with open(report_path, "w") as f:
            f.write(report)
        console.print(f"[green]📄 Test report saved to: {report_path}[/green]")

    def run_evolutionary_cycle(self):
        """Main method to run the full evolutionary testing cycle"""
        console.print("\n[bold]🔄 Agentic Test Evolution Cycle Started[/bold]\n")

        suites = self.run_tests()
        if not suites:
            console.print("[red]No test results collected. Exiting.[/red]")
            return

        suggestions = self.analyze_results(suites)
        self.visualize_results(suites, suggestions)
        self.save_report(self.generate_test_report(suites))
        self._save_history()

        console.print("\n[bold green]✅ Agentic Test Cycle Complete![/bold green]\n")


def main():
    """Main entry point for agentic test manager"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Agentic Test Manager 2026 - Self-evolving test orchestration"
    )
    parser.add_argument(
        "--pattern", default="tests/test_*.py", help="Test file pattern"
    )
    parser.add_argument(
        "--analyze-only", action="store_true", help="Only analyze existing results"
    )
    parser.add_argument("--suggest", type=str, help="Suggest tests for specific module")
    parser.add_argument(
        "--report-only", action="store_true", help="Only generate report from history"
    )

    args = parser.parse_args()
    manager = AgenticTestManager()

    if args.analyze_only:
        manager._load_history()
        manager.visualize_results(
            manager.suites, manager.analyze_results(manager.suites)
        )
    elif args.suggest:
        console.print(
            Panel.fit(
                "\n".join(manager.suggest_new_tests(args.suggest)),
                title=f"💡 Tests for {args.suggest}",
            )
        )
    elif args.report_only:
        manager._load_history()
        manager.save_report(manager.generate_test_report(manager.suites))
    else:
        manager.run_evolutionary_cycle()


if __name__ == "__main__":
    main()
