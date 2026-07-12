---
name: fpf-updater
description: Build, regenerate, and verify the FPF skill from FPF-Spec.md, and pull new FPF versions from upstream. Use when asked to build, run, rebuild, regenerate, verify, or test the fpf skill, to pull/update FPF to the latest version (which also reports what's new since the last update), to re-split the spec into pattern files after editing FPF-Spec.md, or to check that the FPF skill still works.
---

This unit is **not a runnable app** — it's an 8.7 MB conceptual spec
(`FPF-Spec.md`) plus a build pipeline that splits it into the **`fpf`** skill
(one file per pattern — 280 as of the July 2026 spec, the count grows with the
spec — plus a router index). There is no GUI, server, or port to
drive. The thing you "run" is the **build-and-verify pipeline**, and the handle
is `.claude/skills/fpf-updater/verify.py`: it runs the real generator, then asserts
the output is a working skill (split integrity + the question→index→pattern
navigation loop). Build-only lives at `.claude/skills/fpf/scripts/build_skill.py`.

All paths below are relative to the repo root (the unit).

## Prerequisites

**Python 3.9+, standard library only.** No system packages, no `pip install`, no
build deps were needed.

```bash
python3 --version   # → Python 3.9.6 in this container
```

> The scripts use `str | None` annotations guarded by
> `from __future__ import annotations`, so they run on 3.9. Don't remove that
> import.

## Setup

None. Nothing to install. The generator reads `FPF-Spec.md` and writes into the
`fpf` skill directory.

## Update (pull new FPF version + rebuild + what's-new report)

When asked to "pull the new version of FPF" / "update FPF", do ALL of the
following — pull, rebuild, verify, repackage, and finish with a short
**what's new** summary. Don't stop after the pull.

The repo is a clone of `https://github.com/ailev/FPF.git` (upstream commits
touch `FPF-Spec.md` and `Readme.md`; the `.claude/` skill lives only in local
commits, so rebase keeps them cleanly on top).

Run steps 1–2 as **one shell invocation** — shell state does not survive
across separate tool calls, and `$BEFORE` is consumed at the end:

```bash
# 1. Baseline + rebase onto upstream. Stash only if the tree is dirty and pop
#    only what we pushed — an unconditional push/pop pair on a clean tree
#    pops whatever unrelated stash happens to sit at stash@{0}.
BEFORE=$(git log -1 --format=%H -- .claude/skills/fpf/patterns)
git fetch origin
git log --oneline HEAD..origin/main       # incoming commits → quote in the summary
if ! git diff-index --quiet HEAD; then DIRTY=1; git stash push -m "pre-pull skill edits"; fi
git rebase origin/main
[ -n "$DIRTY" ] && git stash pop

# 2. What's-new inputs. New pattern files are untracked until the user
#    commits, so `git diff --name-status` would miss them — hence comm vs ls.
grep -m1 -i 'Version' FPF-Spec.md                          # new spec version line
OLD=$(git ls-tree --name-only "$BEFORE" -- .claude/skills/fpf/patterns/ | sed 's|.*/||' | sort)
NEW=$(ls .claude/skills/fpf/patterns | sort)
comm -13 <(printf '%s\n' "$OLD") <(printf '%s\n' "$NEW")   # added
comm -23 <(printf '%s\n' "$OLD") <(printf '%s\n' "$NEW")   # removed
git diff --stat "$BEFORE" -- .claude/skills/fpf/patterns | tail -1   # how many existing bodies changed
```

```bash
# 3. Rebuild + verify (must end with ALL checks passed), then repackage
python3 .claude/skills/fpf-updater/verify.py
python3 .claude/skills/fpf/scripts/build_skill.py --zip
head -1 .claude/skills/fpf/patterns/<NEW-ID>.md            # title of each new pattern
```

Report: new spec version, incoming upstream commit subjects, patterns
added/removed (ID + title), rough count of changed existing patterns, and
that verify passed all checks. Leave the result uncommitted unless asked —
the user commits updates as e.g. "Update to FPF to <date>".

## Build

Regenerate the `fpf` skill from the spec (run after editing `FPF-Spec.md`):

```bash
python3 .claude/skills/fpf/scripts/build_skill.py
# → pattern files:  280  -> .../.claude/skills/fpf/patterns   (count as of the July 2026 spec)
# → index (TOC):    699 lines -> .../.claude/skills/fpf/reference/index.md
# → SKILL.md:       pattern count synced to 280 (…)           (only if it was stale)
# → stubs (TOC rows without a body): 5  -> C.1, C.5, C.6, C.9, C.14
```

It **wipes `fpf/patterns/` and `fpf/reference/` first**, so the split never
drifts from the source, and it **rewrites the pattern count stated in
`fpf/SKILL.md`** so the skill's self-description tracks the actual split.
Prove a clean rebuild from nothing:

```bash
rm -rf .claude/skills/fpf/patterns .claude/skills/fpf/reference
python3 .claude/skills/fpf/scripts/build_skill.py
ls .claude/skills/fpf/patterns | wc -l   # → 280 (as of the July 2026 spec)
```

If the spec lives elsewhere: `... build_skill.py --spec /abs/path/FPF-Spec.md`.

## Package (distributable zip)

Never zip the skill directory by hand — a hand-rolled or in-place-updated zip is
exactly how a stale `SKILL.md` and `__MACOSX`/`.obsidian`/`__pycache__` junk
shipped to consumers once. Always:

```bash
python3 .claude/skills/fpf/scripts/build_skill.py --zip
# → archive: 283 files   (pattern count + 3: SKILL.md, index.md, build_skill.py) -> .../.claude/skills/fpf.zip
```

`--zip` rebuilds first, then writes the archive **from scratch** with only
`SKILL.md`, `patterns/*.md`, `reference/index.md`, and `scripts/build_skill.py`.
Note the packaged skill has no `FPF-Spec.md` and no `fpf-updater` sibling —
`fpf/SKILL.md`'s Maintenance section says so explicitly.

## Run (agent path)

`verify.py` is the driver. It builds, then validates the result — use this as
the regression check after any spec or generator change:

```bash
python3 .claude/skills/fpf-updater/verify.py
```

Expected output (exit 0; pattern counts shown are as of the July 2026 spec — they grow with it):

```
[PASS] generator exits 0  — rc=0
[PASS] pattern count >= 200  — got 280
[PASS] tricky IDs all emitted  — 8 ok
[PASS] no Part/Cluster heading leaked into a pattern
[PASS] exactly one pattern heading per file
[PASS] filename matches the heading ID inside
[PASS] reference/index.md exists
[PASS] index carries the TOC router table
[PASS] router routes 'badge' question to A.6 + A.10  — ['A.10', 'A.6']
[PASS] loaded A.6 body carries the status/register discipline (the answer)
[PASS] large pattern C.27 is section-readable (:1/:4/Conformance)  — 13 sections
[PASS] every pattern file is a verbatim copy of its FPF-Spec.md slice  — 280 files match spec byte-for-byte
[PASS] SKILL.md's stated pattern count matches the actual files  — stated [280] vs actual 280
[PASS] SKILL.md quick-map IDs exist (and no stale 'stub' claims)  — 20 rows ok

== 14/14 checks passed ==
```

| check | guards against |
|---|---|
| generator exits 0 / count ≥ 200 | spec markers renamed; mass split failure |
| tricky IDs emitted | hyphen IDs (`A.19.SOURCE-SET-SPACE-SUBSTRATE`), em-dash sep (`A.6.B —`), `G.Core` |
| no Part/Cluster leak · one heading/file · filename==ID | boundary-detection regressions in the splitter |
| index carries TOC · routes 'badge' → A.6+A.10 | the router lost the navigation columns |
| A.6 body carries the answer · C.27 section-readable | a pattern body is empty/truncated; large patterns stay sectioned |
| every file is a verbatim copy of its spec slice | a body truncated / corrupted / whitespace-drifted vs `FPF-Spec.md` (all files, not just spot-checks) |
| SKILL.md count matches · quick-map IDs exist, no stale stub claims | the spec grows but SKILL.md keeps the old count / calls now-authored patterns "stubs" (the 244→277 / "D.1–D.4 are stubs" regression) |

It passes `--spec` straight through to the generator:

```bash
python3 .claude/skills/fpf-updater/verify.py --spec /abs/path/FPF-Spec.md
```

## Test

`verify.py` **is** the test (14 checks, exit 0/non-0). To confirm it actually
has teeth, point it at a spec with no Table of Content — it must fail:

```bash
printf '# broken: no TOC, no patterns\n' > /tmp/fpf-broken-spec.md
python3 .claude/skills/fpf-updater/verify.py --spec /tmp/fpf-broken-spec.md
echo $?                                   # → 1  (FAIL: generator exits 0)
python3 .claude/skills/fpf-updater/verify.py  # → 14/14, restores from the real spec
rm -f /tmp/fpf-broken-spec.md
```

> A `--spec` run writes its (possibly broken) output into `fpf/`. A plain
> `verify.py` run rebuilds from the real spec, so the broken-spec test
> self-heals when you re-run without `--spec`, as above.

## Gotchas

- **A local hook may reject bare `python3`.** If a command fails with
  "Use `uv run python3 …` instead", prefix the same command with `uv run`
  — the scripts themselves are stdlib-only and don't care which launcher runs them.
- **Not an app — no screenshot, no server.** The driver is a build+verify smoke
  test (CLI/library shape), not a UI harness. Don't go looking for a window.
- **The build is destructive.** Every `build_skill.py` run deletes
  `fpf/patterns/*.md` before writing. A `--spec` pointed at the wrong file
  silently replaces the good split until you re-run against the real spec.
- **The biggest patterns exceed one `Read`** (>25k tokens): `E.10`, `C.29`,
  `C.27`, `E.19` — with `C.2.P`, `E.8`, `E.18`, `A.6.P` just under. Read them by
  `### <ID>:N` section (Problem frame, Solution, Conformance Checklist). verify
  check #11 keeps `C.27` sectioned.
- **The splitter keys on literal spec markers** — `# Table of Content`,
  `# **Preface**`, and `## <ID>` heading lines (IDs may carry hyphens or an
  em-dash separator). The malformed `# | Block …` lexicon-table lines are
  deliberately *not* treated as boundaries. Rename a marker and the split breaks;
  verify's boundary/alignment checks catch it.
- **Bash cwd persists across calls in this harness.** `cd` into `patterns/` then
  using a relative path bites you. The scripts resolve every path from
  `__file__`, so run them from anywhere — prefer that over `cd`.

## Troubleshooting

- **`error: could not locate FPF-Spec.md`** — run from inside the repo, or pass
  `--spec /abs/path/FPF-Spec.md`.
- **`error: could not find Table of Content / Preface markers in spec`** — the
  spec's `# Table of Content` or `# **Preface**` heading was renamed. Restore it,
  or update the markers in `build_skill.py`.
- **verify FAIL `exactly one pattern heading per file` / `filename matches the
  heading ID`** — a new `##`-level heading style in the spec broke boundary
  detection. Open the named file, diff against the spec, adjust `ID_RE` / the
  boundary regex in `build_skill.py`.
- **verify FAIL `router routes 'badge'…`** — the index's A.6/A.10 keyword rows
  changed. If intentional, update the probe in `verify.py`.
- **pattern count below the floor (200)** — a large spec restructure or a
  splitter regression; read the generator's stdout count and the spec's heading
  shape.
