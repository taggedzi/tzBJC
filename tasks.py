# Path: tasks.py
"""Tasks for invoking tasks using Invoke."""
import re
import shutil
import os
import toml
from pathlib import Path
import subprocess
import sys
import tempfile
from invoke import Exit, task

PYPROJECT_PATH = Path("pyproject.toml")
INIT_PATH = Path("src/tzBJC/__init__.py")


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


def validate_version(version):
    """Accept plain, canonical major.minor.patch versions only."""
    if not re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", version):
        raise Exit("Version must be major.minor.patch, for example 0.2.18.", code=1)
    return tuple(int(part) for part in version.split("."))


def get_current_version():
    return toml.load(PYPROJECT_PATH)["project"]["version"]


def check_versions(version):
    validate_version(version)
    init = INIT_PATH.read_text(encoding="utf-8")
    matches = re.findall(r'^__version__\s*=\s*[\'"]([^\'"]+)[\'"]\s*$', init, re.M)
    if get_current_version() != version or matches != [version]:
        raise Exit("Version mismatch. Run prepare-release and review both version files.", code=1)


@task
def prepare_release(c, version):  # pylint: disable=unused-argument
    """Update both version files for review; do not commit, tag, or push."""
    requested = validate_version(version)
    if requested < validate_version(get_current_version()):
        raise Exit("The new version cannot be lower than the current version.", code=1)
    project = PYPROJECT_PATH.read_text(encoding="utf-8")
    init = INIT_PATH.read_text(encoding="utf-8")
    project, project_count = re.subn(
        r'^(version\s*=\s*)"[^"\n]+"',
        lambda match: match[1] + f'"{version}"', project, flags=re.M,
    )
    init, init_count = re.subn(
        r'^__version__\s*=\s*[\'"][^\'"\n]+[\'"]',
        f'__version__ = "{version}"', init, flags=re.M,
    )
    if project_count != 1 or init_count != 1:
        raise Exit("Expected exactly one version string in each version file; no files changed.", code=1)
    # Validate both replacements before writing either file, preserving TOML formatting.
    PYPROJECT_PATH.write_bytes(project.encode("utf-8"))
    INIT_PATH.write_bytes(init.encode("utf-8"))
    print(f"Prepared {version}. Update CHANGELOG.md, review, and commit the changes.")


@task
def check_release_tag(c, tag):  # pylint: disable=unused-argument
    """Check that a production or TestPyPI tag matches both package versions."""
    match = re.fullmatch(r"(?:testpypi/)?v(.+)", tag)
    if not match:
        raise Exit("Expected vX.Y.Z or testpypi/vX.Y.Z.", code=1)
    check_versions(match[1])
    print(f"Tag {tag} matches both package versions.")


def run_command(*args, capture=False, env=None):
    """Run argument lists directly, using the active environment on every OS."""
    try:
        result = subprocess.run(
            args, check=True, text=True, capture_output=capture, env=env,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        detail = getattr(error, "stderr", None) or str(error)
        raise Exit(f"Command failed ({args[0]}): {detail.strip()}", code=1) from error
    return result.stdout.strip() if capture else None


def publish_preflight(tag):
    """Require a clean main checkout synchronized with the actual remote."""
    if run_command("git", "status", "--porcelain", "--untracked-files=normal", capture=True):
        raise Exit("Commit or remove pending changes before publishing.", code=1)
    if run_command("git", "branch", "--show-current", capture=True) != "main":
        raise Exit("Publish from main after merging the reviewed release changes.", code=1)
    head = run_command("git", "rev-parse", "HEAD", capture=True)
    remote_main = run_command("git", "ls-remote", "origin", "refs/heads/main", capture=True)
    if not remote_main or remote_main.split()[0] != head:
        raise Exit("Local HEAD must match origin/main. Push or pull the reviewed changes first.", code=1)
    if run_command("git", "tag", "--list", tag, capture=True):
        raise Exit(f"Local tag {tag} exists. Inspect its commit and Actions before retrying.", code=1)
    if run_command("git", "ls-remote", "origin", f"refs/tags/{tag}", capture=True):
        raise Exit(f"Remote tag {tag} already exists; use a new version for changes.", code=1)
    return head


@task(help={
    "version": "Version already prepared in both package files, e.g. 0.2.18.",
    "test": "Target TestPyPI only, using a testpypi/vX.Y.Z tag.",
    "publish": "After validation, create and push the tag to start the upload workflow.",
})
def release(c, version, test=False, publish=False):  # pylint: disable=unused-argument
    """Test, build, and check a release. Add --publish to trigger publication."""
    check_versions(version)
    target = "TestPyPI" if test else "PyPI"
    tag = f"{'testpypi/' if test else ''}v{version}"
    head = publish_preflight(tag) if publish else None
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    run_command(sys.executable, "-m", "pytest", env=env)
    Path("dist").mkdir(exist_ok=True)
    # A fresh directory prevents stale distributions from entering a release.
    output = Path(tempfile.mkdtemp(prefix=f"release-{version}-", dir="dist")).resolve()
    run_command(sys.executable, "-m", "build", "--outdir", str(output))
    artifacts = sorted(output.glob("*.whl")) + sorted(output.glob("*.tar.gz"))
    if len(artifacts) != 2:
        raise Exit(f"Expected one wheel and one source archive in {output}.", code=1)
    run_command(sys.executable, "-m", "twine", "check", *(str(path) for path in artifacts))
    if not publish:
        print(f"Validated {version} for {target}. Artifacts: {output}")
        print(f"To publish: python -m invoke release --version={version}"
              f"{' --test' if test else ''} --publish")
        return
    # Tests/build hooks must not leave changes or move HEAD before tagging.
    if publish_preflight(tag) != head:
        raise Exit("HEAD changed during validation; refusing to tag.", code=1)
    run_command("git", "tag", "-a", tag, head, "-m", f"Release {tag}")
    try:
        run_command("git", "-c", "push.followTags=false", "push", "origin", f"refs/tags/{tag}")
    except Exit as error:
        raise Exit(
            f"Tag {tag} remains local. Check origin and Actions; if the push did not arrive, "
            f"retry with: git -c push.followTags=false push origin refs/tags/{tag}", code=1,
        ) from error
    print(f"Pushed {tag}. The {target} workflow will validate and upload the package.")
    print("Check completion at https://github.com/taggedzi/tzBJC/actions")
