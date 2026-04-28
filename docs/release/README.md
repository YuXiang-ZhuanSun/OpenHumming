# Release Kit

This folder collects the materials needed to ship OpenHumming as a polished GitHub release.

## Contents

- [v1.0.0-release-notes.md](v1.0.0-release-notes.md): release notes ready for the GitHub Releases page.
- [v1.0.0-pr-body.md](v1.0.0-pr-body.md): polished PR description for the publish branch.
- [v1.0.0-demo-script.md](v1.0.0-demo-script.md): live demo flow, recording order, and talking points.
- [v1.0.0-social-copy.md](v1.0.0-social-copy.md): launch copy for GitHub, X, LinkedIn, and a longer post.

## Launch Checklist

1. Run validation:
   - `python -m pytest -q`
   - `python -m ruff check .`
   - `python -m build`
2. Refresh the real demo artifacts:
   - `python scripts/run_real_demos.py`
3. Push the release branch and open a draft PR.
4. Paste the body from `v1.0.0-pr-body.md`.
5. Merge, create a `v1.0.0` tag, and paste `v1.0.0-release-notes.md` into GitHub Releases.
