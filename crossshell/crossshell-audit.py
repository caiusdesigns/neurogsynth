#!/usr/bin/env python3
"""Offline Bash-to-PowerShell conversion preflight.

This is intentionally a conservative static scanner, not an automatic
translator. It identifies constructs that need deliberate conversion and
produces a scope summary suitable for a human-reviewed port.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    line: int
    title: str
    evidence: str
    guidance: str


@dataclass(frozen=True)
class Rule:
    rule: str
    severity: str
    title: str
    pattern: re.Pattern[str]
    guidance: str


def _rule(rule: str, severity: str, title: str, pattern: str, guidance: str) -> Rule:
    return Rule(rule, severity, title, re.compile(pattern), guidance)


RULES = (
    _rule("shell.process_substitution", "high", "Process substitution", r"<\(|>\(",
          "Replace with a pipeline, temporary file, or explicit .NET stream."),
    _rule("shell.eval", "high", "Dynamic evaluation", r"(^|[;&|]\s*)eval\s+",
          "Do not transliterate eval. Model the intended command and validate every argument."),
    _rule("shell.source", "medium", "Sourced shell state", r"^\s*(source\s+|\.\s+[^./])",
          "Use PowerShell dot-sourcing and verify which variables or functions must persist."),
    _rule("shell.trap", "medium", "Signal or exit trap", r"(^|[;&|]\s*)trap\s+",
          "Use try/finally for cleanup; map signals only where PowerShell supports the behavior."),
    _rule("shell.strict_mode", "low", "Bash strict mode", r"^\s*set\s+-[^#\n]*[eu]|pipefail",
          "Use Set-StrictMode, $ErrorActionPreference, and explicit native-command exit checks."),
    _rule("shell.array", "medium", "Bash array syntax", r"\$\{[^}]+\[@\]\}|\b[a-zA-Z_][\w]*=\([^)]*\)",
          "Convert to PowerShell arrays and preserve quoting and empty-element behavior."),
    _rule("shell.command_substitution", "medium", "Command substitution", r"\$\([^)]*\)|`[^`]+`",
          "Use $(...) in PowerShell, then verify whether the result should be text, lines, or objects."),
    _rule("shell.parameter_expansion", "medium", "Advanced parameter expansion", r"\$\{[^}]+(:-|:=|:\?|%{1,2}|#{1,2}|//)[^}]*\}",
          "Replace with explicit null/default checks or string/path operations."),
    _rule("shell.test", "medium", "Shell conditional expression", r"\[\[|(^|\s)\[\s+[^]]+\s+\]",
          "Map file and string tests to Test-Path and PowerShell comparison operators."),
    _rule("shell.loop", "low", "Shell loop", r"^\s*(for|while|until|select)\b",
          "Prefer object pipelines or explicit foreach/while blocks; preserve failure behavior."),
    _rule("shell.pipeline", "medium", "Native command pipeline", r"[^|]\|[^|]",
          "PowerShell pipelines pass objects between cmdlets but text between native tools; test every boundary."),
    _rule("shell.redirect", "low", "File descriptor redirection", r"(?:^|\s)(?:\d?>|\d?>>|\d>&\d|&>)",
          "Map output/error streams explicitly and preserve append versus overwrite semantics."),
    _rule("tool.text_unix", "medium", "Unix text-processing utility", r"(^|[;&|]\s*)(awk|sed|grep|cut|tr|xargs)\b",
          "Choose PowerShell object/text cmdlets or retain the dependency explicitly."),
    _rule("tool.files_unix", "medium", "Unix file utility", r"\b(find|chmod|chown|ln|readlink|stat)\b",
          "Map to Get-ChildItem/.NET APIs and document Windows permission or link differences."),
    _rule("tool.network", "medium", "Network command", r"(^|[;&|]\s*)(curl|wget|ssh|scp|rsync)\b",
          "Decide between native executables and PowerShell cmdlets; test auth, errors, and binary transfers."),
    _rule("privilege.sudo", "high", "Privilege escalation", r"(^|[;&|]\s*)sudo\b",
          "Do not emulate silently. Define elevation requirements and least-privilege behavior."),
    _rule("platform.proc", "high", "Unix pseudo-filesystem dependency", r"/(proc|sys|dev)(/|\b)",
          "This behavior is platform-specific and needs a Windows-native design, not syntax translation."),
    _rule("platform.path", "low", "Unix absolute path", r"(?<![\w.])/(etc|var|tmp|opt|usr|home)/",
          "Make the location configurable and use Join-Path or platform environment folders."),
    _rule("shell.heredoc", "medium", "Here-document", r"<<-?\s*['\"]?[A-Za-z_][\w]*",
          "Convert to a here-string and verify interpolation and final-newline behavior."),
)


def _code_without_comments(line: str) -> str:
    """Remove ordinary comments while preserving a shebang and # inside quotes.

    This is deliberately small and safe: an unmatched quote simply keeps the rest
    of the line, preventing a false negative.
    """
    if line.startswith("#!"):
        return line
    quote: str | None = None
    escaped = False
    out: list[str] = []
    for i, char in enumerate(line):
        if escaped:
            out.append(char)
            escaped = False
            continue
        if char == "\\" and quote != "'":
            out.append(char)
            escaped = True
            continue
        if char in ("'", '"'):
            if quote == char:
                quote = None
            elif quote is None:
                quote = char
            out.append(char)
            continue
        if char == "#" and quote is None and (i == 0 or line[i - 1].isspace()):
            break
        out.append(char)
    return "".join(out)


def scan_text(text: str) -> list[Finding]:
    findings: list[Finding] = []
    for number, raw in enumerate(text.splitlines(), 1):
        code = _code_without_comments(raw)
        if not code.strip():
            continue
        for rule in RULES:
            match = rule.pattern.search(code)
            if match:
                evidence = match.group(0).strip() or code.strip()
                findings.append(Finding(rule.rule, rule.severity, number, rule.title,
                                        evidence[:120], rule.guidance))
    return findings


def summary(text: str, findings: Iterable[Finding], source: str) -> dict:
    items = list(findings)
    counts = {severity: sum(f.severity == severity for f in items)
              for severity in ("high", "medium", "low")}
    nonblank = sum(bool(line.strip()) for line in text.splitlines())
    score = counts["high"] * 5 + counts["medium"] * 2 + counts["low"]
    complexity = "high" if counts["high"] or score >= 18 else "medium" if score >= 6 else "low"
    return {
        "source": source,
        "nonblank_lines": nonblank,
        "finding_count": len(items),
        "counts": counts,
        "conversion_complexity": complexity,
        "findings": [asdict(item) for item in items],
        "disclaimer": "Static preflight only; execute and compare the original and port in safe test environments.",
    }


def markdown(report: dict) -> str:
    c = report["counts"]
    lines = [
        "# CrossShell conversion preflight",
        "",
        f"- Source: `{report['source']}`",
        f"- Nonblank lines: {report['nonblank_lines']}",
        f"- Estimated conversion complexity: **{report['conversion_complexity']}**",
        f"- Findings: {report['finding_count']} ({c['high']} high, {c['medium']} medium, {c['low']} low)",
        "",
        "## Findings",
        "",
    ]
    if not report["findings"]:
        lines.append("No known conversion hotspots were detected. Manual behavior testing is still required.")
    for item in report["findings"]:
        lines.extend([
            f"### Line {item['line']}: {item['title']} ({item['severity']})",
            "",
            f"Evidence: `{item['evidence'].replace('`', '')}`",
            "",
            item["guidance"],
            "",
        ])
    lines.extend(["## Important", "", report["disclaimer"], ""])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scan a Bash script for constructs that need deliberate PowerShell conversion."
    )
    parser.add_argument("script", help="Bash script to inspect, or - for stdin")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", "-o", help="Write the report to this file instead of stdout")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.script == "-":
            text, source = sys.stdin.read(), "stdin"
        else:
            path = Path(args.script)
            text, source = path.read_text(encoding="utf-8"), str(path)
    except (OSError, UnicodeError) as exc:
        print(f"crossshell-audit: {exc}", file=sys.stderr)
        return 2

    report = summary(text, scan_text(text), source)
    rendered = json.dumps(report, indent=2) + "\n" if args.format == "json" else markdown(report)
    if args.output:
        try:
            Path(args.output).write_text(rendered, encoding="utf-8")
        except OSError as exc:
            print(f"crossshell-audit: {exc}", file=sys.stderr)
            return 2
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
