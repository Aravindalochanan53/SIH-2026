"""
Acceptance Test 22: Verify that NO deprecated legacy name string exists anywhere in the project.
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

EXCLUDED_DIRS = {".git", ".pytest_cache", "node_modules", "dist", ".system_generated", "logs", "__pycache__", ".venv"}
EXCLUDED_EXTENSIONS = {".pyc", ".png", ".jpg", ".ttf", ".woff", ".woff2", ".db", ".sqlite"}


def test_no_legacy_name_in_project():
    """TEST 22: No legacy name string exists anywhere in project files."""
    term_parts = [
        ("v", "a", "a", "n", "i", " ", "s", "e", "t", "u"),
        ("v", "a", "a", "n", "i", "_", "s", "e", "t", "u"),
        ("v", "a", "a", "n", "i", "-", "s", "e", "t", "u"),
        ("v", "a", "a", "n", "i", "s", "e", "t", "u"),
    ]
    forbidden_terms = ["".join(p) for p in term_parts]
    violations = []

    current_file = Path(__file__).resolve()

    for file_path in BASE_DIR.rglob("*"):
        if file_path.is_file() and file_path.resolve() != current_file:
            # Skip excluded paths
            if any(part in EXCLUDED_DIRS for part in file_path.parts):
                continue
            if file_path.suffix in EXCLUDED_EXTENSIONS:
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore").lower()
                for term in forbidden_terms:
                    if term in content:
                        violations.append(f"{file_path.relative_to(BASE_DIR)} contains '{term}'")
            except Exception:
                pass

    assert not violations, f"Found forbidden terms in:\n" + "\n".join(violations)
