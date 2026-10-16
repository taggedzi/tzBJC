# Changelog

## 0.2.18 — Unreleased

### Fixed

- Replace the legacy release task with separate version preparation, local
  validation, and explicit `--publish` steps. Use GitHub Actions for uploads,
  and separate TestPyPI tags from production tags.
- Require tests and package metadata checks in both publication workflows.
- Pin GitHub Actions to full commit SHAs and support retrying an existing
  TestPyPI tag using the corrected workflow from `main`.

- Keep Base64 padding at the end of the encoded payload. Previously, files
  spanning compression chunks could fail to decode or fail checksum validation.
  Added regression coverage for several chunk sizes and incompressible data.
- Align package Python requirements with pinned PySide6 6.9.0: Python 3.9–3.13.
- Upgrade development pytest to 9.0.3 to address the temporary-directory
  vulnerability (development now requires Python 3.10 or newer).
- Restrict GitHub Actions workflow permissions.

### Documentation

- Rewrite the README around installation, CLI, GUI, and library use.
- Replace the text flowchart with an SVG diagram and add project status badges.
- Describe checksums accurately, document memory and trust constraints, and
  correct the CLI command names.
- Document the repaired Invoke release process, publication targets, and recovery steps.

## 0.2.17

Previous tagged release. See the
[commit comparison](https://github.com/taggedzi/tzBJC/compare/v0.2.17...HEAD)
for changes since that version.
