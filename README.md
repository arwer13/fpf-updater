# fpf-updater

A [Claude Code](https://claude.com/claude-code) skill that turns a clone of
[ailev/FPF](https://github.com/ailev/FPF) (the First Principles Framework,
an 8.7 MB single-file spec) into an agent-usable **`fpf` skill** — one file
per pattern plus a router index — and keeps it current.

What it does, on "update FPF" / "rebuild the fpf skill":

- pulls the latest `FPF-Spec.md` from upstream (rebase, stash-safe),
- splits it into `.claude/skills/fpf/` — 280+ pattern files + `reference/index.md`,
- runs 14 verification checks (every pattern file is compared **byte-for-byte**
  against its spec slice; the router and self-description are probed too),
- reports what's new since your last update (spec version, added/removed
  patterns, changed bodies).

## Install

```bash
git clone https://github.com/ailev/FPF.git && cd FPF
mkdir -p .claude/skills
cp -R /path/to/this/repo/fpf-updater .claude/skills/
```

Then in Claude Code, inside the FPF clone: ask to **"build the fpf skill"**
(first run bootstraps everything from the bundled seed generator) or
**"update FPF"** later. Without an agent:

```bash
python3 .claude/skills/fpf-updater/verify.py   # build + 14 checks, exit 0 = green
```

## Layout

- `fpf-updater/SKILL.md` — the runbook (build / verify / package / update).
- `fpf-updater/verify.py` — the driver: runs the generator, then proves the
  output is a working skill.
- `fpf-updater/seed/` — seed copies of the generator (`build_skill.py`) and
  the fpf skill's `SKILL.md`, installed into `.claude/skills/fpf/` on first
  run when absent (after that, the copies inside the generated `fpf` skill
  are the ones that run and ship; the build keeps their counts synced).

Requires Python 3.9+, standard library only.
