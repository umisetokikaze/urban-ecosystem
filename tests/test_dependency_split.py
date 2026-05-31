"""Dependency split guardrails for runtime vs dev/test requirements."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _requirement_entries(path: Path) -> list[str]:
    entries: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        entries.append(stripped)
    return entries


def test_runtime_requirements_exclude_dev_test_tools() -> None:
    """Cloud Run runtime requirements must not install pytest or Playwright."""
    entries = _requirement_entries(PROJECT_ROOT / "requirements.txt")
    normalized = "\n".join(entries).lower()

    assert "pytest" not in normalized
    assert "playwright" not in normalized


def test_dev_requirements_include_runtime_and_test_tools() -> None:
    """Local dev/CI requirements should layer test tools on top of runtime deps."""
    entries = _requirement_entries(PROJECT_ROOT / "requirements-dev.txt")
    normalized = "\n".join(entries).lower()

    assert "-r requirements.txt" in entries
    assert "pytest" in normalized
    assert "playwright" in normalized


def test_dockerfile_installs_runtime_requirements_only() -> None:
    """Production image should install runtime deps, not dev/test deps."""
    dockerfile = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "pip install --no-cache-dir -r requirements.txt" in dockerfile
    assert "requirements-dev.txt" not in dockerfile


def test_ci_installs_dev_requirements() -> None:
    """CI needs dev requirements so pytest and Playwright are available."""
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )

    assert "requirements-dev.txt" in workflow
    assert "python -m pip install -r requirements-dev.txt" in workflow
