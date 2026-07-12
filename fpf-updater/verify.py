#!/usr/bin/env python3
"""
verify.py — build the `fpf` skill from FPF-Spec.md and prove it actually works.

This is the driver for the `fpf-updater` skill. It does what a human would do by
hand after editing the spec, but as a repeatable regression check:

  1. runs the real generator (fpf/scripts/build_skill.py) as a subprocess,
  2. asserts the emitted split (count floor, tricky IDs, boundary integrity,
     filename<->content alignment, and that every file is a verbatim copy of
     its FPF-Spec.md slice),
  3. asserts the router (reference/index.md) carries the TOC,
  4. drives the progressive-disclosure loop on a real question
     (question -> grep index -> load the pattern body -> find the answer),
  5. checks a large pattern is section-readable (the skill tells agents to read
     big patterns by `### <ID>:N` section).

Exit 0 = all green. Non-zero = something regressed; the failing check is printed.

Usage (from the repo root, or anywhere):
    python3 .claude/skills/fpf-updater/verify.py
    python3 .claude/skills/fpf-updater/verify.py --spec /path/to/FPF-Spec.md
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent.parent          # .../.claude/skills
FPF = SKILLS_DIR / "fpf"
GENERATOR = FPF / "scripts" / "build_skill.py"
PATTERNS = FPF / "patterns"
INDEX = FPF / "reference" / "index.md"

# Standalone bootstrap: in a fresh clone of the FPF repo the `fpf` skill (and
# with it the generator) doesn't exist yet. The published fpf-updater package
# bundles a seed copy of build_skill.py; install it into place and let the
# build create the rest. In the source repo the seed dir doesn't exist and the
# generator is always present, so this is a no-op there.
_SEED_DIR = Path(__file__).resolve().parent / "seed"
for _src, _dst in ((_SEED_DIR / "build_skill.py", GENERATOR),
                   (_SEED_DIR / "fpf-SKILL.md", FPF / "SKILL.md")):
    if _src.is_file() and not _dst.is_file():
        _dst.parent.mkdir(parents=True, exist_ok=True)
        _dst.write_bytes(_src.read_bytes())

# Reuse the generator's own grammar + spec locator so the faithful-copy check
# re-slices FPF-Spec.md exactly the way the splitter does — no parallel grammar
# that could drift out of sync and raise false mismatches.
sys.path.insert(0, str(GENERATOR.parent))
from build_skill import (  # noqa: E402
    find_spec as _find_spec,
    PATTERN_HEADING_RE as _HEAD_RE,
    ID_RE as _ID_RE,
    ANY_H2_RE as _ANY_H2_RE,
    PART_CLUSTER_H1_RE as _GEN_PART_RE,
    SKILL_COUNT_RES as _COUNT_RES,
)

MIN_PATTERNS = 200  # floor; the spec evolves, but a big drop means a split bug
TRICKY_IDS = [
    "A.1", "E.2", "A.6.B", "A.6.3.CR", "G.Core",
    "A.19.SOURCE-SET-SPACE-SUBSTRATE", "C.30.TFS-REL", "E.17.AUD.OOTD",
]
ID_HEADING_RE = re.compile(r"^##\s+([A-K]\.[A-Za-z0-9][A-Za-z0-9.\-]*)\b")
PART_CLUSTER_H1_RE = re.compile(r"^#\s+\**\s*(Part|Cluster|Preface)\b")

results: list[tuple[bool, str]] = []


def check(ok: bool, label: str, detail: str = "") -> bool:
    results.append((ok, label))
    mark = "PASS" if ok else "FAIL"
    line = f"[{mark}] {label}"
    if detail:
        line += f"  — {detail}"
    print(line)
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--spec", help="path to FPF-Spec.md (passed through to generator)")
    args = ap.parse_args()

    print("== fpf-updater verify ==\n")

    # 1. Drive the real generator.
    cmd = [sys.executable, str(GENERATOR)]
    if args.spec:
        cmd += ["--spec", args.spec]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if not check(proc.returncode == 0, "generator exits 0",
                 f"rc={proc.returncode}"):
        print(proc.stderr.strip()[:800])
        return summary()
    m = re.search(r"pattern files:\s*(\d+)", proc.stdout)
    n = int(m.group(1)) if m else len(list(PATTERNS.glob("*.md")))
    check(n >= MIN_PATTERNS, f"pattern count >= {MIN_PATTERNS}", f"got {n}")

    # 2a. Tricky IDs each produced a file.
    missing = [i for i in TRICKY_IDS if not (PATTERNS / f"{i}.md").is_file()]
    check(not missing, "tricky IDs all emitted",
          "missing: " + ", ".join(missing) if missing else f"{len(TRICKY_IDS)} ok")

    # 2b. Boundary integrity + filename<->content alignment across ALL files.
    bad_boundary, bad_align, multi_heading = [], [], []
    for f in sorted(PATTERNS.glob("*.md")):
        lines = f.read_text(encoding="utf-8").splitlines()
        id_headings = [m.group(1) for m in
                       (ID_HEADING_RE.match(ln) for ln in lines) if m]
        if any(PART_CLUSTER_H1_RE.match(ln) for ln in lines):
            bad_boundary.append(f.name)
        if len(id_headings) != 1:
            multi_heading.append(f"{f.name}({len(id_headings)})")
        elif id_headings[0] != f.stem:
            bad_align.append(f"{f.name}!={id_headings[0]}")
    check(not bad_boundary, "no Part/Cluster heading leaked into a pattern",
          ", ".join(bad_boundary[:5]))
    check(not multi_heading, "exactly one pattern heading per file",
          ", ".join(multi_heading[:5]))
    check(not bad_align, "filename matches the heading ID inside",
          ", ".join(bad_align[:5]))

    # 3. Router carries the TOC.
    idx = INDEX.read_text(encoding="utf-8") if INDEX.is_file() else ""
    check(bool(idx), "reference/index.md exists")
    check("Keywords & Search Queries" in idx and "| A.1 " in idx,
          "index carries the TOC router table")

    # 4. Progressive-disclosure loop on a real question.
    #    Q: "is a green PASS badge evidence the check passed?"
    routed = [ln.split("|")[1].strip() for ln in idx.splitlines()
              if "badge" in ln.lower() and ln.startswith("|")]
    routed_ids = {r for r in routed if re.match(r"^[A-K]\.", r)}
    check({"A.6", "A.10"} <= routed_ids,
          "router routes 'badge' question to A.6 + A.10", str(sorted(routed_ids)))
    a6 = (PATTERNS / "A.6.md").read_text(encoding="utf-8") if (PATTERNS / "A.6.md").is_file() else ""
    check("### A.6:" in a6 and re.search(r"register|status display|badge", a6, re.I) is not None,
          "loaded A.6 body carries the status/register discipline (the answer)")

    # 5. A large pattern is section-readable.
    c27 = (PATTERNS / "C.27.md").read_text(encoding="utf-8") if (PATTERNS / "C.27.md").is_file() else ""
    secs = re.findall(r"^### (C\.27:[0-9A-Za-z]+)", c27, re.M)
    check("C.27:1" in secs and "C.27:4" in secs and any("7" in s for s in secs),
          "large pattern C.27 is section-readable (:1/:4/Conformance)",
          f"{len(secs)} sections")

    # 6. Faithful copy: every emitted file is byte-for-byte its spec slice.
    #    Re-extract each pattern's span from FPF-Spec.md with the generator's own
    #    grammar, then compare to the file on disk. This is the check that ties
    #    patterns/<ID>.md back to the source — it catches truncated/corrupted
    #    bodies, dedup drops, and whitespace/encoding drift that the structural
    #    checks (one-heading-per-file, filename==ID) cannot see.
    spec_path = _find_spec(args.spec, GENERATOR.parent)
    spec_lines = spec_path.read_text(encoding="utf-8").splitlines(keepends=True)
    starts: dict[str, int] = {}
    boundaries: list[int] = []
    for i, ln in enumerate(spec_lines):
        if _ANY_H2_RE.match(ln) or _GEN_PART_RE.match(ln):
            boundaries.append(i)
        m = _HEAD_RE.match(ln)
        if m and _ID_RE.match(m.group(1)):
            starts.setdefault(m.group(1), i)  # keep-first, mirroring the generator

    def expected_body(pid: str) -> str | None:
        s = starts.get(pid)
        if s is None:
            return None
        e = next((b for b in boundaries if b > s), len(spec_lines))
        return "".join(spec_lines[s:e]).rstrip("\n") + "\n"

    differ, no_source = [], []
    files = sorted(PATTERNS.glob("*.md"))
    for f in files:
        exp = expected_body(f.stem)
        if exp is None:
            no_source.append(f.stem)
        elif f.read_text(encoding="utf-8") != exp:
            differ.append(f.stem)
    if not differ and not no_source:
        detail = f"{len(files)} files match spec byte-for-byte"
    else:
        detail = (f"{len(differ)} differ {differ[:4]}"
                  f" · {len(no_source)} no spec source {no_source[:4]}")
    check(not differ and not no_source,
          "every pattern file is a verbatim copy of its FPF-Spec.md slice", detail)

    # 7. SKILL.md self-description is not stale.
    #    (Guards the regression where the spec grew 244 -> 277 patterns and
    #    D.1–D.4 gained bodies, but SKILL.md kept the old count + stub claims.)
    skill_md = (FPF / "SKILL.md").read_text(encoding="utf-8") if (FPF / "SKILL.md").is_file() else ""
    # Same regexes the generator patches with — a parallel grammar here would
    # drift the moment the SKILL.md wording changes.
    stated = {int(m.group(0)) for m in (rx.search(skill_md) for rx in _COUNT_RES) if m}
    actual = len(files)
    check(bool(stated) and stated == {actual},
          "SKILL.md's stated pattern count matches the actual files",
          f"stated {sorted(stated)} vs actual {actual}")

    # Scope the scan to the quick-map table so other tables, or prose that
    # happens to contain the word "stub", can't trip the check.
    quick_map = re.search(r"^## Quick map.*?(?=^## |\Z)", skill_md, re.M | re.S)
    quick_rows = [ln for ln in (quick_map.group(0) if quick_map else "").splitlines()
                  if ln.startswith("|") and "`" in ln]
    checked = 0
    missing_unmarked, stale_stub_claims = [], []
    for row in quick_rows:
        ids = [t for t in re.findall(r"`([^`]+)`", row) if _ID_RE.match(t)]
        if not ids:
            continue
        checked += 1
        absent = [i for i in ids if not (PATTERNS / f"{i}.md").is_file()]
        if absent and "stub" not in row.lower():
            missing_unmarked += absent
        if "stub" in row.lower() and not absent:
            stale_stub_claims.append(row.split("|")[1].strip()[:40])
    problems = []
    if quick_map is None:
        problems.append("no '## Quick map' section found")
    if missing_unmarked:
        problems.append(f"missing: {missing_unmarked[:6]}")
    if stale_stub_claims:
        problems.append(f"stale stub rows: {stale_stub_claims[:3]}")
    check(not problems,
          "SKILL.md quick-map IDs exist (and no stale 'stub' claims)",
          "; ".join(problems) or f"{checked} rows ok")

    return summary()


def summary() -> int:
    passed = sum(1 for ok, _ in results if ok)
    total = len(results)
    print(f"\n== {passed}/{total} checks passed ==")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
