# Releasing tzBJC

Use the Invoke tasks from the repository root in an activated Python 3.10?3.13
virtual environment. Install the development and release tools once:

```sh
python -m pip install -e ".[dev]"
```

## 1. Prepare the version

```sh
python -m invoke prepare-release --version=0.2.18
```

This updates `pyproject.toml` and `src/tzBJC/__init__.py` together, preserving the
TOML layout. It does not commit, tag, or push. Running it for the current version
is allowed; a lower version or a malformed version fails with a nonzero exit code.

Update `CHANGELOG.md`, review the diff, then commit and merge the release changes
to `main`. Use patch increments for compatible fixes and maintenance, and minor
increments for new features. Review compatibility explicitly for breaking changes.
Replace `0.2.18` in these examples for future releases.

## 2. Validate locally

```sh
python -m invoke release --version=0.2.18
```

The default command checks both version strings, runs the full test suite with
Qt in offscreen mode, builds a wheel and source archive in a fresh directory
under `dist/`, and runs `twine check` on those two artifacts. It does not create
a tag or access the remote. You can validate uncommitted work this way.
Build isolation may download build dependencies, so network access is needed.

The command uses the active Python environment and argument lists directly,
without Unix cleanup commands or shell wildcards. Failed checks stop the process
with a nonzero exit code. Add `--test` to preview the TestPyPI target.

## 3. Publish

From a clean `main` checkout that matches the current `origin/main` commit:

```sh
python -m invoke release --version=0.2.18 --publish
```

This repeats validation, creates the annotated tag `v0.2.18`, and pushes only
that tag to `origin`. It checks the actual remote branch and tag state before
validation and again before tagging. Pending changes, an existing tag, a failed
remote lookup, or a checkout that differs from `origin/main` stop publication.
Commit and push the release changes first; the task never pushes a branch.

GitHub Actions then checks the tag against both version files, runs the tests,
builds the package, checks its metadata, and uploads to **PyPI only**. A successful
local command means the workflow was triggered; publication completes asynchronously.
Check the [Actions page](https://github.com/taggedzi/tzBJC/actions) for the result.

### TestPyPI trial

To publish to TestPyPI instead:

```sh
python -m invoke release --version=0.2.18 --test --publish
```

This pushes `testpypi/v0.2.18`, which triggers **only TestPyPI**. Production uses
`v0.2.18`, so you can test the same version first and publish it to PyPI afterward.
The task does not upload packages locally, avoiding duplicate uploads.

| Destination | Tag pattern | Required repository secret |
| --- | --- | --- |
| PyPI | `vX.Y.Z` | `PYPI_API_TOKEN` |
| TestPyPI | `testpypi/vX.Y.Z` | `TEST_PYPI_API_TOKEN` |

Configure the appropriate secret under the repository's Actions secrets before
publishing. Merge these workflow changes before using the new process; the
workflows in the tagged commit determine where a tag is published.

The repository must allow GitHub-owned actions, with full-SHA pinning required.
All `uses:` references in the checked-in workflows are pinned to exact commits.

### Recovering from failures

If tests, build, or metadata checks fail locally, fix the issue and rerun. No tag
has been created. The task retains its build artifacts in the printed directory.

If the tag push fails, the local tag remains for inspection. Check Actions and
`git ls-remote origin refs/tags/v0.2.18` to see whether it arrived. If it did not,
retry `git -c push.followTags=false push origin refs/tags/v0.2.18`. For TestPyPI, use
`refs/tags/testpypi/v0.2.18` in both commands. The release task refuses an existing
tag rather than silently replacing it.

If Actions fails before upload, fix an external issue such as a missing secret
and rerun the failed job. If a package version was already uploaded, do not move
its tag or overwrite the published version; prepare a new patch release for code
changes. PyPI does not allow replacing an existing distribution.

If a TestPyPI tag points to an older, broken workflow, rerunning that run still
uses the old workflow. After fixing and pushing the workflow on `main`, use
the manual retry to build the existing tag with the corrected workflow:

```sh
gh workflow run testpypi-publish.yml --ref main -f release_tag=testpypi/v0.2.18
```

This publishes to TestPyPI only and does not move or replace the tag. The manual
retry is intended for failures before any distribution was uploaded.

## Verify publication

Confirm the version appears on [PyPI](https://pypi.org/project/tzBJC/) or
[TestPyPI](https://test.pypi.org/project/tzBJC/). For a production release, install
in a fresh virtual environment and check:

```sh
python -m pip install tzBJC==0.2.18
python -c "import tzBJC; print(tzBJC.__version__)"
tzBJC-cli --help
```

Run an encode/decode round trip. Optionally create a GitHub Release from the tag
using the changelog; the workflows do not create one automatically.

For task options, run `python -m invoke --help release`.
