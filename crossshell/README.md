# CrossShell

CrossShell is a free, offline Bash-to-PowerShell conversion preflight plus a
fixed-scope reviewed conversion service.

The preflight scanner flags constructs that need deliberate porting: process
substitution, traps, strict mode, parameter expansion, pipelines, Unix text and
file utilities, privilege changes, platform paths, here-documents, and more. It
does not execute the script, access the network, or upload code.

```bash
curl -O https://www.neurogsynth.com/crossshell/crossshell-audit.py
python3 crossshell-audit.py deploy.sh -o preflight.md
```

- [Run the free preflight](https://www.neurogsynth.com/crossshell/)
- [CrossShell v1.0.0 release](https://github.com/caiusdesigns/neurogsynth/releases/tag/crossshell-v1.0.0)
- [Review the worked example](https://github.com/caiusdesigns/neurogsynth/tree/main/crossshell/examples)
- [Ask about a public script](https://github.com/caiusdesigns/neurogsynth/issues/new?template=crossshell-order.yml)

Never post credentials, tokens, private keys, personal data, private code, or
internal infrastructure details in a public issue.
