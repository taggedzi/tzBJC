"""Release checks must fail before any tag or upload can be triggered."""
import os
import subprocess
from pathlib import Path

import pytest
from invoke import Context, Exit

import tasks


@pytest.fixture
def release_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("src/tzBJC").mkdir(parents=True)
    Path("pyproject.toml").write_text(
        '# Keep this formatting\n[project]\nversion = "0.2.18"\n', encoding="utf-8",
    )
    Path("src/tzBJC/__init__.py").write_text('__version__ = "0.2.18"\n', encoding="utf-8")
    return tmp_path


def test_prepare_updates_both_versions_without_git(release_project):
    tasks.prepare_release(Context(), "0.2.19")
    tasks.check_versions("0.2.19")
    assert Path("pyproject.toml").read_text().startswith("# Keep this formatting\n")


@pytest.mark.parametrize("version", ["01.2.3", "1.2", "v1.2.3", "1.2.3;echo", "0.2.17"])
def test_prepare_rejects_invalid_or_older_version(release_project, version):
    before = Path("pyproject.toml").read_bytes()
    with pytest.raises(Exit):
        tasks.prepare_release(Context(), version)
    assert Path("pyproject.toml").read_bytes() == before


def test_prepare_checks_both_files_before_writing(release_project):
    Path("src/tzBJC/__init__.py").write_text("# Missing version\n")
    before = Path("pyproject.toml").read_bytes()
    with pytest.raises(Exit):
        tasks.prepare_release(Context(), "0.2.19")
    assert Path("pyproject.toml").read_bytes() == before


@pytest.mark.parametrize("tag", ["v0.2.18", "testpypi/v0.2.18"])
def test_release_tag_matches_versions(release_project, tag):
    tasks.check_release_tag(Context(), tag)


@pytest.mark.parametrize("tag", ["v0.2.19", "testpypi/v0.2.19", "test/v0.2.18", "v01.2.18"])
def test_wrong_tags_are_rejected(release_project, tag):
    with pytest.raises(Exit):
        tasks.check_release_tag(Context(), tag)


def fake_validation(monkeypatch, commands, failure=None):
    def run(*args, **kwargs):
        commands.append(args)
        if args[:3] == (tasks.sys.executable, "-m", failure):
            raise Exit("Validation failed", code=1)
        if args[:3] == (tasks.sys.executable, "-m", "build"):
            output = Path(args[-1])
            (output / "tzbjc-0.2.18-py3-none-any.whl").touch()
            (output / "tzbjc-0.2.18.tar.gz").touch()
        return ""
    monkeypatch.setattr(tasks, "run_command", run)


def test_default_release_validates_without_git_or_upload(release_project, monkeypatch, capsys):
    commands = []
    fake_validation(monkeypatch, commands)
    tasks.release(Context(), "0.2.18")
    assert [cmd[2] for cmd in commands] == ["pytest", "build", "twine"]
    assert commands[-1][3] == "check"
    assert "--publish" in capsys.readouterr().out


@pytest.mark.parametrize("test, tag", [(False, "v0.2.18"), (True, "testpypi/v0.2.18")])
def test_publish_pushes_only_target_tag_after_checks(release_project, monkeypatch, test, tag):
    commands = []
    fake_validation(monkeypatch, commands)
    monkeypatch.setattr(tasks, "publish_preflight", lambda actual: "abc123" if actual == tag else None)
    tasks.release(Context(), "0.2.18", test=test, publish=True)
    assert commands[-2] == ("git", "tag", "-a", tag, "abc123", "-m", f"Release {tag}")
    assert commands[-1] == ("git", "-c", "push.followTags=false", "push", "origin", f"refs/tags/{tag}")
    assert not any("upload" in cmd for cmd in commands)


@pytest.mark.parametrize("failure", ["pytest", "build", "twine"])
def test_failed_validation_never_creates_tag(release_project, monkeypatch, failure):
    commands = []
    fake_validation(monkeypatch, commands, failure)
    monkeypatch.setattr(tasks, "publish_preflight", lambda tag: "abc123")
    with pytest.raises(Exit):
        tasks.release(Context(), "0.2.18", publish=True)
    assert not any(cmd[0] == "git" for cmd in commands)


@pytest.mark.parametrize("failure", ["dirty", "branch", "behind", "local-tag", "remote-tag", "offline"])
def test_publish_preflight_rejects_unsafe_state(monkeypatch, failure):
    def git(*args, **kwargs):
        if args[1] == "status":
            return " M tasks.py" if failure == "dirty" else ""
        if args[1] == "branch":
            return "feature" if failure == "branch" else "main"
        if args[1] == "rev-parse":
            return "abc123"
        if args[1] == "tag":
            return "v0.2.18" if failure == "local-tag" else ""
        if args[1] == "ls-remote":
            if failure == "offline":
                raise Exit("Network failed", code=1)
            if args[-1] == "refs/heads/main":
                return ("older" if failure == "behind" else "abc123") + "\trefs/heads/main"
            return "abc123\trefs/tags/v0.2.18" if failure == "remote-tag" else ""
        raise AssertionError(args)
    monkeypatch.setattr(tasks, "run_command", git)
    with pytest.raises(Exit):
        tasks.publish_preflight("v0.2.18")


def test_command_failure_is_nonzero(monkeypatch):
    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args[0], stderr="failed")
    monkeypatch.setattr(tasks.subprocess, "run", fail)
    with pytest.raises(Exit) as error:
        tasks.run_command("git", "status", capture=True)
    assert error.value.code == 1


def test_version_mismatch_stops_before_commands(release_project, monkeypatch):
    Path("src/tzBJC/__init__.py").write_text('__version__ = "0.2.17"\n')
    commands = []
    fake_validation(monkeypatch, commands)
    with pytest.raises(Exit):
        tasks.release(Context(), "0.2.18", publish=True)
    assert commands == []


def test_head_change_during_checks_prevents_tagging(release_project, monkeypatch):
    commands = []
    fake_validation(monkeypatch, commands)
    heads = iter(["before", "after"])
    monkeypatch.setattr(tasks, "publish_preflight", lambda tag: next(heads))
    with pytest.raises(Exit, match="HEAD changed"):
        tasks.release(Context(), "0.2.18", publish=True)
    assert not any(cmd[0] == "git" for cmd in commands)


def test_push_failure_preserves_tag_and_explains_retry(release_project, monkeypatch):
    commands = []
    fake_validation(monkeypatch, commands)
    validated_run = tasks.run_command
    def run(*args, **kwargs):
        if args[:4] == ("git", "-c", "push.followTags=false", "push"):
            raise Exit("Network failed", code=1)
        return validated_run(*args, **kwargs)
    monkeypatch.setattr(tasks, "run_command", run)
    monkeypatch.setattr(tasks, "publish_preflight", lambda tag: "abc123")
    with pytest.raises(Exit, match="push origin refs/tags/v0.2.18"):
        tasks.release(Context(), "0.2.18", publish=True)
    assert commands[-1][:3] == ("git", "tag", "-a")


@pytest.mark.parametrize("test, tag", [(False, "v0.2.18"), (True, "testpypi/v0.2.18")])
def test_publish_to_local_git_remote(tmp_path, monkeypatch, test, tag):
    """Exercise tag creation/pushing against a local remote, without uploading."""
    # Keep the user's signing, hooks, and remote settings out of the test repo.
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    def git(*args):
        return subprocess.run(["git", *args], check=True, capture_output=True, text=True)
    remote = tmp_path / "remote.git"
    checkout = tmp_path / "checkout"
    git("init", "--bare", str(remote))
    git("init", "-b", "main", str(checkout))
    monkeypatch.chdir(checkout)
    git("config", "user.name", "Release Test")
    git("config", "user.email", "release@example.invalid")
    Path("README.md").write_text("Test release checkout\n")
    Path("pyproject.toml").write_text('[project]\nversion = "0.2.18"\n')
    Path("src/tzBJC").mkdir(parents=True)
    Path("src/tzBJC/__init__.py").write_text('__version__ = "0.2.18"\n')
    Path(".gitignore").write_text("dist/\n")
    git("add", ".")
    git("commit", "-m", "Initial")
    git("remote", "add", "origin", str(remote))
    git("push", "origin", "main")
    head = git("rev-parse", "HEAD").stdout.strip()
    assert tasks.publish_preflight(tag) == head
    actual_run = tasks.run_command
    fake_validation(monkeypatch, [])
    simulated_python = tasks.run_command
    def run(*args, **kwargs):
        if args[0] == "git":
            return actual_run(*args, **kwargs)
        return simulated_python(*args, **kwargs)
    monkeypatch.setattr(tasks, "run_command", run)
    tasks.release(Context(), "0.2.18", test=test, publish=True)
    assert git("rev-parse", f"{tag}^{{commit}}").stdout.strip() == head
    assert git("ls-remote", "origin", f"refs/tags/{tag}").stdout.strip()
    other_tag = "v0.2.18" if test else "testpypi/v0.2.18"
    assert not git("ls-remote", "origin", f"refs/tags/{other_tag}").stdout.strip()
    with pytest.raises(Exit, match="Local tag"):
        tasks.publish_preflight(tag)
