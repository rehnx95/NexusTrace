# Phase 0 Status

## Completed

- Created branch `refactor/pretrained-first` and tag `v0-baseline`.
- Added backend requirement groups for base, pretrained, and development dependencies.
- Added GitHub Actions backend/frontend CI.
- Added a backend pytest smoke test for the documented empty-ingestion baseline.
- Added the leak-check entry point and target skeleton with README stubs.
- Added an untracked backend environment template.

## Baseline Verification

- Frontend production build passes with Vite.
- Leak-check placeholder exits successfully.
- Backend smoke/lint execution could not run locally because the sandbox blocks package installation into the user Python directory.
- GitHub Actions uses Python 3.10 and installs the declared development requirements before running tests and lint.

## Evidence

The live-path review confirmed the baseline issue register remains applicable. No extraction, graph, or frontend behavior was changed in Phase 0.
