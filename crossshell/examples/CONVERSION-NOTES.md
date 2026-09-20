# Example conversion notes

This sample shows the form of a delivered Bash-to-PowerShell port. It is not a
claim that a syntax substitution preserves behavior.

Key decisions:

- The Bash `tar.gz` output becomes a ZIP because `Compress-Archive` is native to
  supported PowerShell installations. A customer who requires `tar.gz` would
  receive a version built around `tar.exe` or a documented dependency.
- `set -euo pipefail` becomes strict mode, stop-on-error behavior, and a
  top-level `try`/`catch`.
- The `ERR` trap becomes explicit error handling.
- `find` and its NUL-delimited pipe become `Get-ChildItem` objects filtered
  before their full paths reach `Compress-Archive`.
- The script resolves and constructs paths explicitly to avoid dependence on
  the caller's current working directory.

Verification checklist:

1. Run both versions against fixtures containing nested directories, spaces,
   Unicode filenames, an empty directory, and a `.git` directory.
2. Confirm the archive contains the intended files and no `.git` content.
3. Confirm a missing source exits nonzero and writes a useful error.
4. Confirm the destination is created when absent.
5. Confirm repeated runs do not overwrite earlier archives.

