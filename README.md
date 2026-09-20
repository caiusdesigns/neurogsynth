# neurogsynth small tools

Small, privacy-conscious tools for working shops, studios, developers, and
operations teams.

## CrossShell

[CrossShell](https://www.neurogsynth.com/crossshell/) checks a Bash script for
constructs that need deliberate PowerShell conversion. The scanner is free,
offline, standard-library-only, and does not execute or upload the target
script.

```bash
curl -O https://www.neurogsynth.com/crossshell/crossshell-audit.py
python3 crossshell-audit.py deploy.sh -o preflight.md
```

A fixed-scope reviewed conversion service is also available from the CrossShell
page. Public scope questions can use the
[CrossShell issue form](https://github.com/caiusdesigns/neurogsynth/issues/new?template=crossshell-order.yml).
The free scanner is versioned as
[CrossShell v1.0.0](https://github.com/caiusdesigns/neurogsynth/releases/tag/crossshell-v1.0.0).

Do not submit secrets, credentials, personal data, private code, or internal
infrastructure details through a public issue.
