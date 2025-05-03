# Path: tasks.py
"""Tasks for invoking tasks using Invoke."""
import shutil
import os
from invoke import task

@task
def setup(c):
    """Install the project in editable mode with dev dependencies."""
    c.run("pip install -e .[dev]")

@task
def test(c):
    """Run tests using pytest."""
    c.run("pytest")

@task
def coverage(c):
    """Run tests with coverage report."""
    c.run("pytest --cov=tzBJC --cov-report=term-missing")

@task
def coverage_html(c):
    """Generate HTML coverage report."""
    c.run("pytest --cov=tzBJC --cov-report=html")
    print("Open htmlcov/index.html in your browser to view the report.")

@task
def build(c):
    """Build the distribution packages."""
    c.run("python -m build")

@task
def clean(c):
    """Remove build artifacts."""
    c.run("rm -rf dist/ build/ *.egg-info htmlcov .pytest_cache")

@task
def cleanpy(c):   # pylint: disable=unused-argument
    """Remove __pycache__ and coverage artifacts."""
    for root, dirs, _ in os.walk("."):
        for d in dirs:
            if d == "__pycache__":
                shutil.rmtree(os.path.join(root, d), ignore_errors=True)
    if os.path.exists(".coverage"):
        os.remove(".coverage")

@task
def freeze(c):
    """Generate requirements.txt from current environment (useful for lockfiles)."""
    c.run("pip freeze > requirements.txt")

@task
def tag_release(c, version):
    """
    Tag a new release and push the tag to GitHub.
    
    Usage:
      invoke tag-release --version=v0.2.0
    """
    if not version.startswith("v"):
        print("❌ Version must start with 'v' (e.g., v0.2.0)")
        return

    print(f"🔖 Tagging release {version}...")
    c.run(f"git tag {version}")
    c.run(f"git push origin {version}")
    print(f"✅ Tag {version} pushed to GitHub.")
    
@task
def push_all(c):
    """
    Push latest commits and all tags to origin.
    
    Usage:
      invoke push-all
    """
    print("📦 Pushing commits to origin...")
    c.run("git push")

    print("🏷️  Pushing tags to origin...")
    c.run("git push --tags")

    print("✅ Push complete.")
