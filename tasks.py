# Path: tasks.py
"""Tasks for invoking tasks using Invoke."""
import re
import shutil
import os
import subprocess
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


def git_output(command):
    """Run a git command and return its output as string."""
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    return result.stdout.strip()

@task
def tag(c, version, branch="main"):
    """
    Tag the current commit with a semantic version and push it.

    Usage:
        invoke tag --version=0.2.3
    Optional:
        --branch=main (default)
    """
    # 1. Validate version format
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        print("❌ Invalid version format. Use semantic versioning like '0.2.3'.")
        return

    tag_name = f"v{version}"

    # 2. Ensure current branch is correct
    current_branch = git_output("git rev-parse --abbrev-ref HEAD")
    if current_branch != branch:
        print(f"❌ You are on branch '{current_branch}', not '{branch}'.")
        print("✅ Use --branch=your-branch to override.")
        return

    # 3. Check for uncommitted changes
    if git_output("git status --porcelain"):
        print("❌ Working directory is not clean. Please commit or stash changes.")
        return

    # 4. Check if tag already exists
    existing_tags = git_output("git tag").splitlines()
    if tag_name in existing_tags:
        print(f"❌ Tag {tag_name} already exists.")
        return

    # 5. Create and push the annotated tag
    print(f"🏷️ Tagging as {tag_name}...")
    c.run(f'git tag -a {tag_name} -m "Release {tag_name}"')
    c.run(f"git push origin {tag_name}")

    print(f"✅ Tag {tag_name} created and pushed successfully.")
    