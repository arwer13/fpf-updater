#!/usr/bin/env python3
"""
build_skill.py — regenerate the FPF skill's progressive-disclosure layers from
the canonical FPF-Spec.md.

It does three things:

  1. Splits every governing pattern body (`## <ID> - Title` ... up to the next
     `##`/Part/Cluster boundary) into one self-contained file under patterns/.
  2. Copies the spec's Table of Content verbatim into reference/index.md and
     prepends a short "how to navigate" header. The TOC is the authors'
     purpose-built router (ID, keywords, search queries, dependency graph), so we
     reuse it rather than re-deriving a second one.
  3. Patches the pattern-file count wherever SKILL.md states it, so the skill's
     self-description never drifts from the actual split.

Re-run this whenever FPF-Spec.md changes:

    python3 .claude/skills/fpf/scripts/build_skill.py
    # or point at a spec explicitly:
    python3 .claude/skills/fpf/scripts/build_skill.py --spec /path/to/FPF-Spec.md
    # optionally also produce a clean distributable archive:
    python3 .claude/skills/fpf/scripts/build_skill.py --zip

The patterns/ directory is fully rebuilt each run (stale files removed), so the
split copy never drifts from the source.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# A pattern heading is `## <ID> ...` whose first whitespace token is an FPF id:
#   a Part letter A-K, a dot, then dotted/hyphenated alnum segments.
#   matches A.1, A.6.B, C.2.P, G.Core, A.19.SOURCE-SET-SPACE-SUBSTRATE, E.17.AUD.OOTD
ID_RE = re.compile(r"^[A-K]\.[A-Za-z0-9][A-Za-z0-9.\-]*$")
PATTERN_HEADING_RE = re.compile(r"^##\s+(\S+)")
# Any h2 OR a Part/Cluster/Preface h1 ends the preceding pattern body.
# (The `# | Block ...` lexicon-table h1s are intentionally NOT boundaries.)
ANY_H2_RE = re.compile(r"^##\s")
PART_CLUSTER_H1_RE = re.compile(r"^#\s+\**\s*(Part|Cluster|Preface)\b")

TOC_START_MARKER = re.compile(r"^#\s+Table of Content\b", re.IGNORECASE)
PREFACE_MARKER = re.compile(r"^#\s+\**\s*Preface\b")

INDEX_HEADER = """\
# FPF Pattern Router (Table of Content)

This is the navigation index for the First Principles Framework. It is copied
verbatim from `FPF-Spec.md` and is the authors' purpose-built router.

**How to use it to find a pattern:**

1. State the live question — what are you trying to *decide, publish, classify,
   or stabilize*? (Not the chapter, the decision.)
2. Scan the **Keywords & Search Queries** column for the row whose wording
   matches your question. That row's **ID** (first column) is your pattern.
3. Open `patterns/<ID>.md` for the full pattern body.
4. Follow the **Dependencies** column (`Builds on` / `Coordinates with` /
   `Prerequisite for`) to pull in neighbouring patterns as needed.

> If `patterns/<ID>.md` does not exist, that row is a **stub** (Status `Stub`/
> `stub`/`Draft` with no authored body yet) — use the row's reminder text and
> its dependencies to reason, and consult the named neighbouring patterns.

Statuses: **Stable** (authoritative), **Draft**/**Transitional stub** (usable,
evolving), **Stub** (placeholder, often no body).

---

"""


def find_spec(explicit: str | None, script_dir: Path) -> Path:
    """Locate FPF-Spec.md: explicit arg, else search upward from script & cwd."""
    if explicit:
        p = Path(explicit).expanduser().resolve()
        if not p.is_file():
            sys.exit(f"error: --spec path not found: {p}")
        return p
    for base in (script_dir, Path.cwd()):
        cur = base.resolve()
        for _ in range(8):
            cand = cur / "FPF-Spec.md"
            if cand.is_file():
                return cand
            if cur.parent == cur:
                break
            cur = cur.parent
    sys.exit(
        "error: could not locate FPF-Spec.md. Pass it explicitly:\n"
        "  python3 build_skill.py --spec /path/to/FPF-Spec.md"
    )


def split_patterns(lines: list[str]) -> list[tuple[str, int, int]]:
    """Return [(id, start_idx, end_idx)] half-open over `lines` (0-based)."""
    boundaries: list[int] = []
    starts: list[tuple[str, int]] = []
    for i, line in enumerate(lines):
        if ANY_H2_RE.match(line) or PART_CLUSTER_H1_RE.match(line):
            boundaries.append(i)
        m = PATTERN_HEADING_RE.match(line)
        if m and ID_RE.match(m.group(1)):
            starts.append((m.group(1), i))
    boundaries = sorted(set(boundaries))
    out: list[tuple[str, int, int]] = []
    for pid, start in starts:
        end = next((b for b in boundaries if b > start), len(lines))
        out.append((pid, start, end))
    return out


def write_index(spec_lines: list[str], ref_dir: Path) -> int:
    """Copy the spec's Table of Content into reference/index.md."""
    toc_start = toc_end = None
    for i, line in enumerate(spec_lines):
        if toc_start is None and TOC_START_MARKER.match(line):
            toc_start = i + 1  # skip the "# Table of Content" line itself
        elif toc_start is not None and PREFACE_MARKER.match(line):
            toc_end = i
            break
    if toc_start is None or toc_end is None:
        sys.exit("error: could not find Table of Content / Preface markers in spec.")
    toc = "".join(spec_lines[toc_start:toc_end]).strip("\n")
    ref_dir.mkdir(parents=True, exist_ok=True)
    (ref_dir / "index.md").write_text(INDEX_HEADER + toc + "\n", encoding="utf-8")
    return toc_end - toc_start


# SKILL.md phrases that carry the pattern-file count. Each regex's numeric
# group is rewritten to the actual count on every build so the skill's
# self-description cannot drift from the split (this is what went stale when
# the spec grew 244 -> 277 patterns).
SKILL_COUNT_RES = [
    re.compile(r"\d+(?= self-contained pattern bodies)"),
    re.compile(r"(?<=rebuilds all )\d+(?= `patterns/\*\.md`)"),
]

# First cell of a TOC row (`| D.1 | ... |`); captured generically and
# validated against ID_RE so the ID grammar lives in exactly one place.
TOC_ROW_ID_RE = re.compile(r"^\|\s*([^|\s]+)\s*\|")


def patch_skill_counts(skill_root: Path, count: int) -> None:
    """Rewrite the stated pattern count inside SKILL.md to the actual count."""
    skill_md = skill_root / "SKILL.md"
    if not skill_md.is_file():
        print("warning: SKILL.md not found; count not patched")
        return
    text = skill_md.read_text(encoding="utf-8")
    new, hits = text, 0
    for rx in SKILL_COUNT_RES:
        new, n = rx.subn(str(count), new)
        hits += n
    if hits == 0:
        print("warning: no count phrases found in SKILL.md; "
              "update SKILL_COUNT_RES if the wording changed")
    elif new != text:
        skill_md.write_text(new, encoding="utf-8")
        print(f"SKILL.md:       pattern count synced to {count} ({hits} places)")


def report_stubs(ref_dir: Path, emitted: set[str]) -> None:
    """List TOC rows that have no pattern file (stubs) — informational."""
    idx = ref_dir / "index.md"
    if not idx.is_file():
        return
    toc_ids = []
    for ln in idx.read_text(encoding="utf-8").splitlines():
        m = TOC_ROW_ID_RE.match(ln)
        if m and ID_RE.match(m.group(1)):
            toc_ids.append(m.group(1))
    stubs = [i for i in toc_ids if i not in emitted]
    print(f"stubs (TOC rows without a body): {len(stubs)}"
          + (f"  -> {', '.join(stubs)}" if stubs else ""))


def write_zip(skill_root: Path, zip_path: Path) -> None:
    """Package a clean, standalone skill archive (no OS/editor/cache junk).

    Built from scratch every time — never updated in place — so the archive can
    not carry a stale SKILL.md or leftover pattern files from a previous build.
    """
    import zipfile

    include = [skill_root / "SKILL.md",
               *sorted((skill_root / "patterns").glob("*.md")),
               skill_root / "reference" / "index.md",
               skill_root / "scripts" / "build_skill.py"]
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in include:
            zf.write(f, Path("fpf") / f.relative_to(skill_root))
    print(f"archive:        {len(include)} files -> {zip_path}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--spec", help="path to FPF-Spec.md (default: search upward)")
    ap.add_argument("--zip", nargs="?", const="", metavar="PATH",
                    help="also write a clean distributable fpf.zip "
                         "(default: next to the skill directory)")
    args = ap.parse_args()

    script_dir = Path(__file__).resolve().parent
    skill_root = script_dir.parent  # .../skills/fpf
    spec_path = find_spec(args.spec, script_dir)
    spec_lines = spec_path.read_text(encoding="utf-8").splitlines(keepends=True)

    patterns_dir = skill_root / "patterns"
    ref_dir = skill_root / "reference"

    # Rebuild patterns/ from scratch so removed/renamed patterns don't linger.
    patterns_dir.mkdir(parents=True, exist_ok=True)
    for old in patterns_dir.glob("*.md"):
        old.unlink()

    patterns = split_patterns(spec_lines)
    seen: dict[str, int] = {}
    for pid, start, end in patterns:
        body = "".join(spec_lines[start:end]).rstrip("\n") + "\n"
        # If an ID somehow repeats, keep the first and warn (do not overwrite).
        if pid in seen:
            print(f"warning: duplicate id {pid} at line {start + 1}; keeping first")
            continue
        seen[pid] = start
        (patterns_dir / f"{pid}.md").write_text(body, encoding="utf-8")

    toc_lines = write_index(spec_lines, ref_dir)

    print(f"spec:           {spec_path}")
    print(f"pattern files:  {len(seen)}  -> {patterns_dir}")
    print(f"index (TOC):    {toc_lines} lines -> {ref_dir / 'index.md'}")

    patch_skill_counts(skill_root, len(seen))
    report_stubs(ref_dir, set(seen))

    if args.zip is not None:
        zip_path = (Path(args.zip).expanduser().resolve() if args.zip
                    else skill_root.parent / "fpf.zip")
        write_zip(skill_root, zip_path)


if __name__ == "__main__":
    main()
